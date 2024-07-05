FROM ghcr.io/commandcracker/ffmpeg:latest AS ffmpeg

FROM ffmpeg AS sanjuuni

ENV SANJUUNI_VERSION=778644b164c8877e56f9f5512480dde857133815

ARG SANJUUNI_SHA512SUM="353b97e53ec2daba3046b3062c8a389c75066ea410f9abe089467a4648e83afe926cd65ad0904a0d59eca0520e3174e0f3190987cfee3abbdc9141a04a80ef1a *sanjuuni.tar.gz"

SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

RUN set -eux; \
  apk add --no-cache --update \
  g++=13.2.1_git20240309-r0 \
  zlib-dev=1.3.1-r1 \
  poco-dev=1.12.4-r0 \
  make=4.4.1-r2; \
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
  apk add --no-cache --update build-base=0.5-r3; \
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
  libffi=3.4.6-r0 libbz2=1.0.8-r6 \
  # sanjuuni requirements
  poco=1.12.4-r0 \
  # ffmpeg requirements
  libgcc=13.2.1_git20240309-r0 \
  libstdc++=13.2.1_git20240309-r0 \
  ca-certificates=20240226-r0 \
  libgomp=13.2.1_git20240309-r0 \
  expat=2.6.2-r0; \
  apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/v3.18/community libssl1.1=1.1.1u-r1 libcrypto1.1=1.1.1u-r1; \
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
