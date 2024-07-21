FROM ghcr.io/commandcracker/ffmpeg:latest AS ffmpeg

FROM ffmpeg AS sanjuuni

ENV SANJUUNI_VERSION=49cb275d4ef64d2bee3d5d2cbc5baf47787bedc2

ARG SANJUUNI_SHA512SUM="22c85f9a5c16c0acb4dde971b64f53e765a8d607065e7a25115103925124e33a0680da3790e85c4343b7d320a0170b6ae096ec7f2b48b22582cf96681fd3a78c *sanjuuni.tar.gz"

SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

RUN set -eux; \
  apk add --no-cache --update \
  g++ \
  zlib-dev \
  poco-dev \
  make; \
  wget -q --output-document=sanjuuni.tar.gz https://github.com/MCJack123/sanjuuni/archive/${SANJUUNI_VERSION}.tar.gz; \
  echo "${SANJUUNI_SHA512SUM}" | sha512sum -c -; \
  mkdir --parents sanjuuni; \
  tar --extract --directory sanjuuni --strip-components=1 --file=sanjuuni.tar.gz; \
  rm sanjuuni.tar.gz;

WORKDIR /sanjuuni

RUN set -eux; \
  ./configure; \
  make

FROM ghcr.io/commandcracker/alpine-pypy3.10-pip:3.20.1-pypy-7.3.14-pip-24.1.1 AS builder

WORKDIR /

COPY requirements.txt .
COPY youcube ./youcube
COPY compile.py .

RUN set -eux; \
  apk add --no-cache --update build-base; \
  pip install --no-cache-dir -U setuptools -r requirements.txt; \
  python3 compile.py; \
  pip uninstall pip -y

FROM alpine:3.20.1

WORKDIR /opt/server

RUN set -eux; \
  apk add --no-cache --update \
  # CVE-2024-5535 TODO: remove when base image is updated
  openssl \
  # pypy requirements
  libffi libbz2 \
  # sanjuuni requirements
  poco \
  # ffmpeg requirements
  libgcc \
  libstdc++ \
  ca-certificates \
  libgomp \
  expat; \
  apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/v3.18/community libssl1.1=1.1.1u-r1 libcrypto1.1=1.1.1u-r1; \
  chown 1000:1000 /opt/server/

COPY --from=builder /opt/pypy /opt/pypy
# add ffmpeg
COPY --from=ffmpeg /usr/local /usr/local
# add sanjuuni
COPY --from=sanjuuni /sanjuuni/sanjuuni /usr/local/bin

ENV \
  # Make sure, that the container is accessible from outside
  HOST=0.0.0.0 \
  # Make sure we use the virtualenv:
  PATH="/opt/pypy/bin:$PATH" \
  # Use ffmpeg libs
  LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64 \
  # yt-dlp cache dir
  XDG_CACHE_HOME="/opt/server/.yt-dlp-cache" \
  # FIXME: Add UVLOOP support for alpine pypy
  SANIC_NO_UVLOOP=true

USER 1000:1000

COPY --from=builder /youcube/__pycache__ /opt/server

ENTRYPOINT ["python3", "youcube.pyc"]
