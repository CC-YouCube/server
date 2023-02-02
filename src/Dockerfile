FROM ghcr.io/commandcracker/ffmpeg:latest AS ffmpeg

FROM ffmpeg as sanjuuni

ENV SANJUUNI_VERSION=0.3

ARG SANJUUNI_SHA512SUM="2aee316cc97f70d0f6935f9126721ae35f96d1570a96a757a5f680493856287c0620ef0ee0dc982d51417aa1a40b57f9e588dc9672c719aaa5e34552163dcd16 *sanjuuni.tar.gz"

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

FROM ghcr.io/commandcracker/alpine-pypy3.9-pip:3.17.1-pypy-7.3.11-pip-22.3.1 AS builder

COPY requirements.txt .
COPY youcube ./youcube
COPY compile.py .

RUN set -eux; \
    apk add --no-cache --update build-base; \
    pip install --no-cache-dir --use-pep517 -U setuptools -r requirements.txt; \
    python3 compile.py; \
    pip uninstall pip -y

FROM alpine:3.17.1

WORKDIR /opt/server

RUN set -eux; \
    apk add --no-cache --update \
    # pypy requirements
    libffi libbz2 \
    # ffmpeg requirements
    libgcc libstdc++ ca-certificates libcrypto1.1 libssl1.1 libgomp expat \
    # sanjuuni requirements
    poco; \
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
    XDG_CACHE_HOME="/opt/server/.yt-dlp-cache"

USER 1000

COPY --from=builder /youcube/__pycache__ /opt/server

ENTRYPOINT ["python3", "youcube.pyc"]
