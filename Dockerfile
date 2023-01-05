FROM python:3.9-slim-bullseye as base

RUN pip install pytest pytest-cases pytest-rerunfailures
RUN apt-get -y update
RUN apt install -y libsm6 \
                libxext6 \
                ffmpeg \
                libfontconfig1 \
                libxrender1 \
                libgl1-mesa-glx \
                libgeos-dev

WORKDIR /usr/src/
COPY requirements.txt /usr/src/
RUN pip install -r requirements.txt
COPY . /usr/src/

RUN python setup.py install

FROM base as dev
RUN pip install -r requirements-dev.txt