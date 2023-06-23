FROM ghcr.io/commandcracker/ffmpeg:latest AS ffmpeg

FROM ffmpeg as sanjuuni

ENV SANJUUNI_VERSION=0.4

ARG SANJUUNI_SHA512SUM="952a6c608d167f37faad53ee7f2e0de8090a02bf73b6455fae7c6b6f648dd6a188e7749fe26caeee85126b2a38d7391389c19afb0100e9962dc551188b9de6ae *sanjuuni.tar.gz"

# TODO: Disable opencl

RUN set -eux; \
    apk add --no-cache --update opencl-dev g++ zlib-dev poco-dev make; \
    wget --output-document=sanjuuni.tar.gz https://github.com/MCJack123/sanjuuni/archive/${SANJUUNI_VERSION}.tar.gz; \
    echo "${SANJUUNI_SHA512SUM}" | sha512sum -c -; \
    mkdir --parents sanjuuni; \
    tar --extract --directory sanjuuni --strip-components=1 --file=sanjuuni.tar.gz; \
    rm sanjuuni.tar.gz;

WORKDIR /sanjuuni

RUN set -eux; \
    ./configure; \
    make

FROM ghcr.io/commandcracker/alpine-pypy3.10-pip:3.18.2-pypy-7.3.12-pip-23.1.2 AS builder

COPY requirements.txt .
COPY youcube ./youcube
COPY compile.py .

RUN set -eux; \
    apk add --no-cache --update build-base; \
    pip install --no-cache-dir -U setuptools -r requirements.txt; \
    python3 compile.py; \
    pip uninstall pip -y

FROM alpine:3.18.2

WORKDIR /opt/server

RUN set -eux; \
    apk add --no-cache --update \
    # pypy requirements
    libffi libbz2 \
    # ffmpeg requirements
    libgcc libstdc++ ca-certificates libcrypto1.1 libssl1.1 libgomp expat \
    # sanjuuni requirements
    poco opencl; \
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
