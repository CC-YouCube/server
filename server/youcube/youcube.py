#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
YouCube Server
"""

# built-in modules
from os.path import join
from os import getenv
from json import loads as load_json
from json.decoder import JSONDecodeError
from logging import Logger
from asyncio import get_event_loop
from typing import Any, Callable
from base64 import b64encode
from shutil import which
from types import UnionType

# pip modules
from aiohttp.web import (
    Request,
    WebSocketResponse,
    Response,
    WSMsgType,
    Application,
    run_app
)

# local modules
from yc_logging import setup_logging, NO_COLOR
from yc_magic import run_function_in_thread_from_async_function
from yc_download import download, DATA_FOLDER, FFMPEG_PATH, SANJUUNI_PATH
from yc_colours import Foreground, RESET
from yc_utils import (
    is_save,
    cap_width_and_height,
    get_video_name,
    get_audio_name
)

VERSION = "0.0.0-poc.0.0.0"
API_VERSION = "0.0.0-poc.0.0.0"  # https://commandcracker.github.io/YouCube/
CHUNK_SIZE = 16 * 1024

# pylint settings
# pylint: disable=pointless-string-statement
# pylint: disable=fixme
# pylint: disable=multiple-statements


def get_vid(vid_file: str, line: int) -> bytes:
    """
    Returns given line of 32vid file
    """

    """
    def get_vid(vid_file: str, tracker: int) -> bytes:
        with open(vid_file, "r", encoding="utf-8") as file:
            file.seek(tracker)
            line = file.readline()
            file.close()
    return line # new tracker = len(line) + old_tracker
    """

    # TODO: read from file.seek(tracker) tracker = size(lines[line]) + tracker
    # TODO: linecache
    with open(vid_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
        out = lines[line]
        file.close()

    return out[:-1]  # remove \n


def get_chunk(media_file: str, chunkindex: int) -> bytes:
    """
    Returns a chunk of the given media file
    """
    with open(media_file, "rb") as file:
        file.seek(chunkindex * CHUNK_SIZE)
        chunk = file.read(CHUNK_SIZE)
        file.close()

    return chunk


def get_peername_host(request: Request) -> str:
    """
    Returns the Host of the web-request
    """
    peername = request.transport.get_extra_info('peername')

    if peername is not None:
        host, *_ = peername
        return host

    return None


class UntrustedProxy(Exception):
    """
    Occurs when someone connects through an untrusted proxy
    """

    def __str__(self) -> str:
        return "A client is not using a trusted proxy!"


def get_client_ip(request: Request, trusted_proxies: list) -> str:
    """
    Returns the real client IP
    """
    peername_host = get_peername_host(request)

    if trusted_proxies is None:
        return peername_host

    if peername_host in trusted_proxies:
        x_forwarded_for = request.headers.get('X-Forwarded-For')

        if x_forwarded_for is not None:
            x_forwarded_for = x_forwarded_for.split(",")[0]

        return x_forwarded_for or request.headers.get('True-Client-Ip')

    raise UntrustedProxy


def assert_resp(
    __obj_name: str,
    __obj: object,
    __class_or_tuple: type | UnionType | tuple[
        type |
        UnionType | tuple[Any, ...], ...
    ]
) -> dict | None:
    """
    "assert" / isinstance that returns a dict that can be send as a ws response
    """
    if not isinstance(__obj, __class_or_tuple):
        return {
            "action": "error",
            "message": f"{__obj_name} must be a {__class_or_tuple.__name__}"
        }
    return None


class Actions:
    """
    Default set of actions
    Every action needs to be called with a message and needs to return a dict response
    """

    # pylint: disable=unused-argument
    # pylint: disable=missing-function-docstring

    @staticmethod
    async def request_media(message: dict, resp: WebSocketResponse):
        loop = get_event_loop()
        # get "url"
        url = message.get("url")
        if error := assert_resp("url", url, str): return error
        # TODO: assert_resp width and height
        return await run_function_in_thread_from_async_function(
            download,
            url,
            resp,
            loop,
            message.get("width"),
            message.get("height")
        )

    @staticmethod
    async def get_chunk(message: dict, resp: WebSocketResponse):
        # get "chunkindex"
        chunkindex = message.get("chunkindex")
        if error := assert_resp("chunkindex", chunkindex, int): return error

        # get "id"
        media_id = message.get("id")
        if error := assert_resp("media_id", media_id, str): return error

        if is_save(media_id):
            file = join(
                DATA_FOLDER,
                get_audio_name(message.get("id"))
            )

            chunk = get_chunk(file, chunkindex)

            if len(chunk) == 0:
                return {
                    "action": "error",
                    "message": "mister, the media has finished playing"
                }

            return {
                "action": "chunk",
                "chunk": b64encode(chunk).decode("ascii")
            }

        return {
            "action": "error",
            "message": "You dare not use special Characters"
        }

    @staticmethod
    async def get_vid(message: dict, resp: WebSocketResponse):
        # get "line"
        lineindex = message.get("line")
        if error := assert_resp("line", lineindex, int): return error

        # get "id"
        media_id = message.get("id")
        if error := assert_resp("id", media_id, str): return error

        # get "width"
        width = message.get('width')
        if error := assert_resp("width", width, int): return error

        # get "height"
        height = message.get('height')
        if error := assert_resp("height", height, int): return error

        # cap height and width
        width, height = cap_width_and_height(width, height)

        if is_save(media_id):
            file = join(
                DATA_FOLDER,
                get_video_name(message.get('id'), width, height)
            )

            return {
                "action": "vid",
                "line": get_vid(file, lineindex)
            }

        return {
            "action": "error",
            "message": "You dare not use special Characters"
        }

    @staticmethod
    async def handshake(message: dict, resp: WebSocketResponse):
        return {
            "action": "handshake",
            "server": {
                "version": VERSION
            },
            "api": {
                "version": API_VERSION
            },
            "capabilities": {
                "video": [
                    "32vid"
                ],
                "audio": [
                    "dfpwm"
                ]
            }
        }

    # pylint: enable=unused-argument
    # pylint: enable=missing-function-docstring


class Server:
    """
    The Web socket server Object
    """

    def __init__(self, logger: Logger, trusted_proxies: list) -> None:
        self.logger = logger
        self.trusted_proxies = trusted_proxies
        self.actions = {}

        # add all actions from default action set

        for method in dir(Actions):
            if not method.startswith('__'):
                self.actions[method] = Actions.__getattribute__(
                    Actions,
                    method
                )

    async def on_shutdown(self, app: Application):
        """
        Clears all web-sockets from the list
        """

        for websocket in app["sockets"]:
            await websocket.close()

    def init(self):
        """
        Initialize the web-socket server
        """
        app = Application()
        app["sockets"] = []
        app.router.add_get("/", self.wshandler)
        app.on_shutdown.append(self.on_shutdown)
        return app

    def register_action(self, name: str, func: Callable[[], Any]):
        """
        Add and action / "endpoint" to the ws server
        """
        if name in self.actions:
            return False, f"action \"{name}\" is already registerd!"
        self.actions[name] = func
        return True

    async def wshandler(self, request: Request):
        """
        Handels web-socket requests
        """
        resp = WebSocketResponse()
        available = resp.can_prepare(request)
        if not available:
            return Response(
                body="You cannot access a WebSocket server directly. You need a WebSocket client.",
                content_type="text"
            )

        await resp.prepare(request)

        try:
            request.app["sockets"].append(resp)

            client_ip = get_client_ip(request, self.trusted_proxies)
            if NO_COLOR:
                prefix = f"[{client_ip}] "
            else:
                prefix = f"{Foreground.BLUE}[{client_ip}]{RESET} "

            self.logger.info(prefix + "Connected!")

            self.logger.debug(
                prefix +
                "My headers are: " +
                str(request.headers)
            )

            async for msg in resp:
                resp: WebSocketResponse
                if msg.type == WSMsgType.TEXT:
                    self.logger.debug(prefix + "Message: " + msg.data)
                    try:
                        message: dict = load_json(msg.data)

                        if message.get("action") in self.actions:
                            response = await self.actions[message.get("action")](message, resp)
                            await resp.send_json(response)
                    except JSONDecodeError:
                        self.logger.debug(prefix + "Faild to parse Json")
                        await resp.send_json({
                            "action": "error",
                            "message": "Faild to parse Json"
                        })

                else:
                    return resp
            return resp

        finally:
            request.app["sockets"].remove(resp)
            self.logger.info(prefix + "Disconnected!")


def main() -> None:
    """
    Run all needed services
    """
    logger = setup_logging()

    if which(FFMPEG_PATH) is None:
        logger.warning("FFmpeg not found.")

    if which(SANJUUNI_PATH) is None:
        logger.warning("Sanjuuni not found.")

    port = int(getenv("PORT", "5000"))
    trusted_proxies = getenv("TRUSTED_PROXIES")

    proxies = None

    if trusted_proxies is not None:
        proxies = []
        for proxy in trusted_proxies.split(","):
            proxies.append(proxy)

    server = Server(logger, proxies)

    if not NO_COLOR:
        print(Foreground.BRIGHT_GREEN, end="")

    run_app(server.init(), port=port)


if __name__ == "__main__":
    main()
