FROM ghcr.io/commandcracker/ffmpeg:latest AS ffmpeg

FROM ffmpeg as sanjuuni

ENV SANJUUNI_VERSION=ed34c266cd489e4db796ca803e247b48b43853e0

ARG SANJUUNI_SHA512SUM="9e482e3b8f8885e8f458856f11d5ee4c27a0aa469b8c54abe1aef943f630ca27eb148c8779ba7a053c1abcce298513e98b614747a77ae1c0cbc86a0a7c95a6d8 *sanjuuni.tar.gz"

RUN set -eux; \
    apk add --no-cache --update g++ zlib-dev poco-dev make; \
    wget --output-document=sanjuuni.tar.gz https://github.com/MCJack123/sanjuuni/archive/${SANJUUNI_VERSION}.tar.gz; \
    echo "${SANJUUNI_SHA512SUM}" | sha512sum -c -; \
    mkdir --parents sanjuuni; \
    tar --extract --directory sanjuuni --strip-components=1 --file=sanjuuni.tar.gz; \
    rm sanjuuni.tar.gz;

WORKDIR /sanjuuni

RUN set -eux; \
    ./configure; \
    make

FROM ghcr.io/commandcracker/alpine-pypy3.10-pip:3.19.0-pypy-7.3.14-pip-23.3.2 AS builder

COPY requirements.txt .
COPY youcube ./youcube
COPY compile.py .

RUN set -eux; \
    apk add --no-cache --update build-base; \
    pip install --no-cache-dir -U setuptools -r requirements.txt; \
    python3 compile.py; \
    pip uninstall pip -y

FROM alpine:3.19.0

WORKDIR /opt/server

RUN set -eux; \
    apk add --no-cache --update \
    # pypy requirements
    libffi libbz2 \
    # sanjuuni requirements
    poco \
    # ffmpeg requirements
    libgcc libstdc++ ca-certificates libgomp expat; \
    apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/v3.18/community libssl1.1 libcrypto1.1; \
    chown 1000 /opt/server/

COPY --from=builder /opt/pypy /opt/pypy
# add ffmpeg
COPY --from=ffmpeg /usr/local /usr/local
# add sanjuuni
COPY --from=sanjuuni /sanjuuni/sanjuuni /usr/local/bin

ENV \
    # Make sure we use the virtualenv:
    PATH="/opt/pypy/bin:$PATH" \
    # Use ffmpeg libs
    LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64 \
    # yt-dlp cache dir
    XDG_CACHE_HOME="/opt/server/.yt-dlp-cache" \
    # FIXME: Add UVLOOP support for alpine pypy
    SANIC_NO_UVLOOP=true

USER 1000

COPY --from=builder /youcube/__pycache__ /opt/server

ENTRYPOINT ["python3", "youcube.pyc"]
