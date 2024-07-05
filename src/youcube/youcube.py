#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouCube Server
"""

# built-in modules
from asyncio import get_event_loop
from base64 import b64encode
from datetime import datetime
from multiprocessing import Manager
from os import getenv, remove
from os.path import exists, join
from shutil import which
from time import sleep
from typing import Any, List, Tuple, Type, Union

# optional pip module
try:
    from orjson import JSONDecodeError, dumps
    from orjson import loads as load_json
except ModuleNotFoundError:
    from json import dumps
    from json import loads as load_json
    from json.decoder import JSONDecodeError

try:
    from types import UnionType
except ImportError:
    UnionType = Union[int, str]


# pip modules
from sanic import Request, Sanic, Websocket
from sanic.compat import open_async
from sanic.exceptions import SanicException
from sanic.handlers import ErrorHandler
from sanic.response import raw, text
from spotipy import MemoryCacheHandler, SpotifyClientCredentials
from spotipy.client import Spotify

# local modules
from yc_colours import RESET, Foreground
from yc_download import DATA_FOLDER, FFMPEG_PATH, SANJUUNI_PATH, download
from yc_logging import NO_COLOR, setup_logging
from yc_magic import run_function_in_thread_from_async_function
from yc_spotify import SpotifyURLProcessor
from yc_utils import cap_width_and_height, get_audio_name, get_video_name, is_save

VERSION = "0.0.0-poc.1.0.2"
API_VERSION = "0.0.0-poc.1.0.0"  # https://commandcracker.github.io/YouCube/

# one dfpwm chunk is 16 bits
CHUNK_SIZE = 16

"""
CHUNKS_AT_ONCE should not be too big, [CHUNK_SIZE * 1024]
because then the CC Computer cant decode the string fast enough!
Also, it should not be too small because then the client
would need to send thousands of WS messages
and that would also slow everything down! [CHUNK_SIZE * 1]
"""
CHUNKS_AT_ONCE = CHUNK_SIZE * 256


FRAMES_AT_ONCE = 10

"""
Ubuntu nvida support fix and maby alpine support ?
us async base64 ?
use HTTP (and Streaming)
Add uvloop support https://github.com/CC-YouCube/server/issues/6
"""

"""
1 dfpwm chunk = 16
MAX_DOWNLOAD = 16 * 1024 * 1024 = 16777216
WEBSOCKET_MESSAGE = 128 * 1024 = 131072
(MAX_DOWNLOAD = 128 * WEBSOCKET_MESSAGE)

the speaker can accept a maximum of 128 x 1024 samples 16KiB

playAudio
This accepts a list of audio samples as amplitudes between -128 and 127.
These are stored in an internal buffer and played back at 48kHz.
If this buffer is full, this function will return false.
"""

"""Related CC-Tweaked issues
Streaming HTTP response https://github.com/cc-tweaked/CC-Tweaked/issues/1181
Speaker Networks        https://github.com/cc-tweaked/CC-Tweaked/issues/1488
Pocket computers do not have many usecases without network access https://github.com/cc-tweaked/CC-Tweaked/issues/1406
Speaker limit to 8      https://github.com/cc-tweaked/CC-Tweaked/issues/1313
Some way to notify player through pocket computer with modem https://github.com/cc-tweaked/CC-Tweaked/issues/1148
Memory limits for computers https://github.com/cc-tweaked/CC-Tweaked/issues/1580
"""

"""TODO: Add those:
AudioDevices:
 - Speaker Note (Sound)  https://tweaked.cc/peripheral/speaker.html
 - Notblock              https://www.youtube.com/watch?v=XY5UvTxD9dA
 - Create Steam whistles https://www.youtube.com/watch?v=dgZ4F7U19do
                         https://github.com/danielathome19/MIDIToComputerCraft/tree/master

Video Formats:
 - 32vid binary https://github.com/MCJack123/sanjuuni
 - qtv          https://github.com/Axisok/qtccv

Audio Formats:
 - DFPWM ffmpeg fallback ? https://github.com/asiekierka/pixmess/blob/master/scraps/aucmp.py
 - PCM
 - NBS  https://github.com/Xella37/NBS-Tunes-CC
 - MIDI https://github.com/OpenPrograms/Sangar-Programs/blob/master/midi.lua
 - XM   https://github.com/MCJack123/tracc

Audio u. Video preview / thumbnail:
 - NFP  https://tweaked.cc/library/cc.image.nft.html
 - bimg https://github.com/SkyTheCodeMaster/bimg
 - as 1 qtv frame
 - as 1 32vid frame
"""

# pylint settings
# pylint: disable=pointless-string-statement
# pylint: disable=fixme
# pylint: disable=multiple-statements

logger = setup_logging()
# TODO: change sanic logging format


async def get_vid(vid_file: str, tracker: int) -> List[str]:
    """Returns given line of 32vid file"""
    async with await open_async(file=vid_file, mode="r", encoding="utf-8") as file:
        await file.seek(tracker)
        lines = []
        for _unused in range(FRAMES_AT_ONCE):
            lines.append((await file.readline())[:-1])  # remove \n

    return lines


async def getchunk(media_file: str, chunkindex: int) -> bytes:
    """Returns a chunk of the given media file"""
    async with await open_async(file=media_file, mode="rb") as file:
        await file.seek(chunkindex * CHUNKS_AT_ONCE)
        return await file.read(CHUNKS_AT_ONCE)


# pylint: enable=redefined-outer-name


def assert_resp(
    __obj_name: str,
    __obj: Any,
    __class_or_tuple: Union[
        Type, UnionType, Tuple[Union[Type, UnionType, Tuple[Any, ...]], ...]
    ],
) -> Union[dict, None]:
    """
    "assert" / isinstance that returns a dict that can be send as a ws response
    """
    if not isinstance(__obj, __class_or_tuple):
        return {
            "action": "error",
            "message": f"{__obj_name} must be a {__class_or_tuple.__name__}",
        }
    return None


# pylint: disable=duplicate-code
spotify_client_id = getenv("SPOTIPY_CLIENT_ID")
spotify_client_secret = getenv("SPOTIPY_CLIENT_SECRET")
# pylint: disable-next=invalid-name
spotipy = None

if spotify_client_id and spotify_client_secret:
    spotipy = Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            cache_handler=MemoryCacheHandler(),
        )
    )

# pylint: disable-next=invalid-name
spotify_url_processor = None
if spotipy:
    spotify_url_processor = SpotifyURLProcessor(spotipy)

# pylint: enable=duplicate-code


class Actions:
    """
    Default set of actions
    Every action needs to be called with a message and needs to return a dict response
    """

    # pylint: disable=missing-function-docstring

    @staticmethod
    async def request_media(message: dict, resp: Websocket, request: Request):
        loop = get_event_loop()
        # get "url"
        url = message.get("url")
        if error := assert_resp("url", url, str):
            return error
        # TODO: assert_resp width and height
        out, files = await run_function_in_thread_from_async_function(
            download,
            url,
            resp,
            loop,
            message.get("width"),
            message.get("height"),
            spotify_url_processor,
        )
        for file in files:
            request.app.shared_ctx.data[file] = datetime.now()
        return out

    @staticmethod
    async def get_chunk(message: dict, _unused, request: Request):
        # get "chunkindex"
        chunkindex = message.get("chunkindex")
        if error := assert_resp("chunkindex", chunkindex, int):
            return error

        # get "id"
        media_id = message.get("id")
        if error := assert_resp("media_id", media_id, str):
            return error

        if is_save(media_id):
            file_name = get_audio_name(message.get("id"))
            file = join(DATA_FOLDER, file_name)

            request.app.shared_ctx.data[file_name] = datetime.now()
            chunk = await getchunk(file, chunkindex)

            return {"action": "chunk", "chunk": b64encode(chunk).decode("ascii")}
        logger.warning("User tried to use special Characters")
        return {"action": "error", "message": "You dare not use special Characters"}

    @staticmethod
    async def get_vid(message: dict, _unused, request: Request):
        # get "line"
        tracker = message.get("tracker")
        if error := assert_resp("tracker", tracker, int):
            return error

        # get "id"
        media_id = message.get("id")
        if error := assert_resp("id", media_id, str):
            return error

        # get "width"
        width = message.get("width")
        if error := assert_resp("width", width, int):
            return error

        # get "height"
        height = message.get("height")
        if error := assert_resp("height", height, int):
            return error

        # cap height and width
        width, height = cap_width_and_height(width, height)

        if is_save(media_id):
            file_name = get_video_name(message.get("id"), width, height)
            file = join(DATA_FOLDER, file_name)

            request.app.shared_ctx.data[file_name] = datetime.now()

            return {"action": "vid", "lines": await get_vid(file, tracker)}

        return {"action": "error", "message": "You dare not use special Characters"}

    @staticmethod
    async def handshake(*_unused):
        return {
            "action": "handshake",
            "server": {"version": VERSION},
            "api": {"version": API_VERSION},
            "capabilities": {"video": ["32vid"], "audio": ["dfpwm"]},
        }

    # pylint: enable=missing-function-docstring


class CustomErrorHandler(ErrorHandler):
    """Error handler for sanic"""

    def default(self, request: Request, exception: Union[SanicException, Exception]):
        """handles errors that have no error handlers assigned"""

        if isinstance(exception, SanicException) and exception.status_code == 426:
            # TODO: Respond with nice html that tells the user how to install YC
            return text(
                "You cannot access a YouCube server directly. "
                "You need the YouCube client. "
                "See https://youcube.madefor.cc/guides/client/installation/"
            )

        return super().default(request, exception)


app = Sanic("youcube")
app.error_handler = CustomErrorHandler()
# FIXME: The Client is not Responsing to Websocket pings
app.config.WEBSOCKET_PING_INTERVAL = 0
# FIXME: Add UVLOOP support for alpine pypy
if getenv("SANIC_NO_UVLOOP"):
    app.config.USE_UVLOOP = False

actions = {}

# add all actions from default action set
for method in dir(Actions):
    if not method.startswith("__"):
        actions[method] = getattr(Actions, method)


DATA_CACHE_CLEANUP_INTERVAL = int(getenv("DATA_CACHE_CLEANUP_INTERVAL", "300"))
DATA_CACHE_CLEANUP_AFTER = int(getenv("DATA_CACHE_CLEANUP_AFTER", "3600"))


def data_cache_cleaner(data: dict):
    """
    Checks for outdated cache entries every DATA_CACHE_CLEANUP_INTERVAL (default 300) Seconds and
    deletes them if they have not been used for DATA_CACHE_CLEANUP_AFTER (default 3600) Seconds.
    """
    try:
        while True:
            sleep(DATA_CACHE_CLEANUP_INTERVAL)
            for file_name, last_used in data.items():
                if (
                    datetime.now() - last_used
                ).total_seconds() > DATA_CACHE_CLEANUP_AFTER:
                    file_path = join(DATA_FOLDER, file_name)
                    if exists(file_path):
                        remove(file_path)
                        logger.debug('Deleted "%s"', file_name)
                    data.pop(file_name)

    except KeyboardInterrupt:
        pass


# pylint: disable=redefined-outer-name
@app.main_process_ready
async def ready(app: Sanic, _):
    """See https://sanic.dev/en/guide/basics/listeners.html"""
    if DATA_CACHE_CLEANUP_INTERVAL > 0 and DATA_CACHE_CLEANUP_AFTER > 0:
        app.manager.manage(
            "Data-Cache-Cleaner", data_cache_cleaner, {"data": app.shared_ctx.data}
        )


@app.main_process_start
async def main_start(app: Sanic):
    """See https://sanic.dev/en/guide/basics/listeners.html"""
    app.shared_ctx.data = Manager().dict()

    if which(FFMPEG_PATH) is None:
        logger.warning("FFmpeg not found.")

    if which(SANJUUNI_PATH) is None:
        logger.warning("Sanjuuni not found.")

    if spotipy:
        logger.info("Spotipy Enabled")
    else:
        logger.info("Spotipy Disabled")


@app.route("/dfpwm/<id:str>/<chunkindex:int>")
async def stream_dfpwm(request: Request, id: str, chunkindex: int):
    return raw(await getchunk(join(DATA_FOLDER, get_audio_name(id)), chunkindex))


@app.route("/32vid/<id:str>/<width:int>/<height:int>/<tracker:int>")  # , stream=True
async def stream_32vid(
    request: Request, id: str, width: int, height: int, tracker: int
):
    return raw(
        "\n".join(
            await get_vid(join(DATA_FOLDER, get_video_name(id, width, height)), tracker)
        )
    )


""""
from sanic import response
@app.route("/dfpwm/<id:str>")
async def stream_dfpwm(request: Request, id: str):
    file_name = get_audio_name(id)
    file = join(DATA_FOLDER, get_audio_name(id))
    return await response.file_stream(
        file,
        chunk_size=CHUNKS_AT_ONCE,
        mime_type="application/metalink4+xml",
        headers={
            "Content-Disposition": f'Attachment; filename="{file_name}"',
            "Content-Type": "application/metalink4+xml",
        },
    )

@app.route("/32vid/<id:str>/<width:int>/<height:int>", stream=True)
async def stream_32vid(request: Request, id: str, width: int, height: int):
    file_name = get_video_name(id, width, height)
    file = join(
        DATA_FOLDER,
        file_name
    )
    return await response.file_stream(
        file,
        chunk_size=10,
        mime_type="application/metalink4+xml",
        headers={
            "Content-Disposition": f'Attachment; filename="{file_name}"',
            "Content-Type": "application/metalink4+xml",
        },
    )
"""
# pylint: enable=redefined-outer-name


@app.websocket("/")
# pylint: disable-next=invalid-name
async def wshandler(request: Request, ws: Websocket):
    """Handels web-socket requests"""
    if NO_COLOR:
        prefix = f"[{request.client_ip}] "
    else:
        prefix = f"{Foreground.BLUE}[{request.client_ip}]{RESET} "

    logger.info("%sConnected!", prefix)

    logger.debug("%sMy headers are: %s", prefix, request.headers)

    while True:
        message = await ws.recv()
        logger.debug("%sMessage: %s", prefix, message)

        try:
            message: dict = load_json(message)
        except JSONDecodeError:
            logger.debug("%sFaild to parse Json", prefix)
            await ws.send(dumps({"action": "error", "message": "Faild to parse Json"}))

        if message.get("action") in actions:
            response = await actions[message.get("action")](message, ws, request)
            await ws.send(dumps(response))


def main() -> None:
    """
    Run all needed services
    """
    port = int(getenv("PORT", "5000"))
    host = getenv("HOST", "127.0.0.1")
    fast = not getenv("NO_FAST")

    app.run(host=host, port=port, fast=fast, access_log=True)


if __name__ == "__main__":
    main()
