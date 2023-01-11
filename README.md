# YouCube Server

[![Python Version: 3.7+](https://img.shields.io/badge/Python-3.7+-green?style=for-the-badge&logo=Python&logoColor=white)](https://www.python.org/downloads/)
[![Python Lint Workflow Status](https://img.shields.io/github/actions/workflow/status/CC-YouCube/server/pylint.yml?branch=main&label=Python%20Lint&logo=github&style=for-the-badge)](https://github.com/CC-YouCube/server/actions/workflows/pylint.yml)

![preview](.README/preview-server.png)

YouCube has a some public servers, which you can use if you don't want to host your own server. \
The client has the public servers set by default, so you can just run the client, and you're good to go. \
Moor Information about the servers can be seen on the [doc](https://youcube.madefor.cc/api/).

## Requirements

- [yt-dlp/FFmpeg](https://github.com/yt-dlp/FFmpeg-Builds) / [FFmpeg 5.1+](https://ffmpeg.org/)
- [sanjuuni](https://github.com/MCJack123/sanjuuni)
- [Python 3.7+](https://www.python.org/downloads/)
  - [aiohttp](https://pypi.org/project/aiohttp/)
  - [yt-dlp](https://pypi.org/project/yt-dlp/)

You can install the required packages with [pip](https://pip.pypa.io/en/stable/installation/) by running:

```shell
pip install -r server/requirements.txt
```

## Starting the Server

```bash
python server/youcube.py
```

## Environment variables

Environment variables you can use to configure the server.

| Variable          | Default    | Description                                 |
|-------------------|------------|---------------------------------------------|
| `HOST`            | `0.0.0.0`  | The host where the web server runs on.      |
| `PORT`            | `5000`     | The port where the web server should run on |
| `TRUSTED_PROXIES` |            | Trusted proxies (separated by comma`,`)     |
| `FFMPEG_PATH`     | `ffmpeg`   | Path to the FFmpeg executable               |
| `SANJUUNI_PATH`   | `sanjuuni` | Path to the Sanjuuni executable             |
| `NO_COLOR`        | `False`    | Disable colored output                      |
| `LOGLEVEL`        | `DEBUG`    | Python Log level of the main logger         |

## Docker Compose

```yml
version: "2.0"
services:
  youcube:
    image: ghcr.io/commandcracker/youcube:main
    restart: always
    hostname: youcube
    ports:
      - 5000:5000
```
