FROM ghcr.io/commandcracker/ffmpeg:latest AS ffmpeg

FROM ffmpeg as sanjuuni

ENV SANJUUNI_VERSION=0.4

ARG SANJUUNI_SHA512SUM="952a6c608d167f37faad53ee7f2e0de8090a02bf73b6455fae7c6b6f648dd6a188e7749fe26caeee85126b2a38d7391389c19afb0100e9962dc551188b9de6ae *sanjuuni.tar.gz"

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

FROM mcr.microsoft.com/vscode/devcontainers/base:alpine-3.17

RUN set -eux; \
    apk add --no-cache --update \
    # python
    python3 py3-pip gcc libc-dev \
    # ffmpeg requirements
    libgcc libstdc++ ca-certificates libcrypto1.1 libssl1.1 libgomp expat \
    # sanjuuni requirements
    poco opencl \
    # utils
    make; \
    pip install --no-cache-dir --upgrade pip; \
    # python-is-python3
    ln -sf python3 /usr/bin/python

# add ffmpeg
COPY --from=ffmpeg /usr/local /usr/local

# add sanjuuni
COPY --from=sanjuuni /sanjuuni/sanjuuni /usr/local/bin

# Use ffmpeg libs
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64
