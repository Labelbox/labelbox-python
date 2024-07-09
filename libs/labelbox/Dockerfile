# https://github.com/ucyo/python-package-template/blob/master/Dockerfile
FROM python:3.8-slim as rye

ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PATH="/home/python/.local/bin:/home/python/.rye/shims:$PATH" \
    PIP_NO_CACHE_DIR="false" \
    RYE_VERSION="0.36.0" \
    RYE_INSTALL_OPTION="--yes" \
    LABELBOX_TEST_ENVIRON="prod"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    inotify-tools \
    make \
    # cv2
    libsm6 \
    libxext6 \
    ffmpeg \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    libgeos-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 python && \
    useradd  --uid 1000 --gid python --shell /bin/bash --create-home python

USER 1000
WORKDIR /home/python/

RUN curl -sSf https://rye.astral.sh/get | bash -

COPY --chown=python:python . /home/python/labelbox-python/
WORKDIR /home/python/labelbox-python

RUN rye config --set-bool behavior.global-python=true && \
    rye config --set-bool behavior.use-uv=true && \
    rye pin 3.8 && \
    rye sync

CMD cd libs/labelbox && rye run integration && rye sync -f --features labelbox/data && rye run unit && rye run data
