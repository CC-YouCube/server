# YouCube Server

[![Python Version: 3.7+]](https://www.python.org/downloads/)
[![Python Lint Workflow Status]](https://github.com/CC-YouCube/server/actions/workflows/pylint.yml)

![preview]

YouCube has a some public servers, which you can use if you don't want to host your own server. \
The client has the public servers set by default, so you can just run the client, and you're good to go. \
Moor Information about the servers can be seen on the [doc].

## Requirements

- [yt-dlp/FFmpeg] / [FFmpeg 5.1+]
- [sanjuuni]
- [Python 3.7+]
  - [sanic]
  - [yt-dlp]
  - [ujson] (Optional)
  - [spotipy]

You can install the required packages with [pip] by running:

```shell
pip install -r src/requirements.txt
```

## Starting the Server

```bash
python src/youcube.py
```

## Environment variables

Environment variables you can use to configure the server.

| Variable                | Default    | Description                                       |
|-------------------------|------------|---------------------------------------------------|
| `HOST`                  | `0.0.0.0`  | The host where the web server runs on.            |
| `PORT`                  | `5000`     | The port where the web server should run on       |
| `TRUSTED_PROXIES`       |            | Trusted proxies (separated by comma`,`)           |
| `FFMPEG_PATH`           | `ffmpeg`   | Path to the FFmpeg executable                     |
| `SANJUUNI_PATH`         | `sanjuuni` | Path to the Sanjuuni executable                   |
| `NO_COLOR`              | `False`    | Disable colored output                            |
| `LOGLEVEL`              | `DEBUG`    | Python Log level of the main logger               |
| `DISABLE_OPENCL`        | `False`    | Disables sanjuuni GPU acceleration                |
| `NO_FAST`               | `False`    | Disable Sanic worker processes maximization       |
| `SPOTIPY_CLIENT_ID`     |            | The Client ID from your [spotify application]     |
| `SPOTIPY_CLIENT_SECRET` |            | The Client Secret from your [spotify application] |

## Docker Compose

```yml
version: "2.0"
services:
  youcube:
    image: ghcr.io/cc-youcube/youcube:latest
    restart: always
    hostname: youcube
    ports:
      - 5000:5000
```

[spotify application]: https://developer.spotify.com/dashboard/applications
[pip]: https://pip.pypa.io/en/stable/installation
[yt-dlp/FFmpeg]: https://github.com/yt-dlp/FFmpeg-Builds
[FFmpeg 5.1+]: https://ffmpeg.org
[sanjuuni]: https://github.com/MCJack123/sanjuuni
[Python 3.7+]: https://www.python.org/downloads
[sanic]: https://sanic.dev
[yt-dlp]: https://pypi.org/project/yt-dlp
[ujson]: https://pypi.org/project/ujson
[spotipy]: https://pypi.org/project/spotipy
[doc]: https://youcube.madefor.cc/api
[preview]: .README/preview-server.png
[Python Version: 3.7+]: https://img.shields.io/badge/Python-3.7+-green?style=for-the-badge&logo=Python&logoColor=white
[Python Lint Workflow Status]: https://img.shields.io/github/actions/workflow/status/CC-YouCube/server/pylint.yml?branch=main&label=Python%20Lint&logo=github&style=for-the-badge
