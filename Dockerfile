FROM python:3.9-slim-bullseye

RUN pip install pytest=="7.4.4" pytest-cases pytest-rerunfailures pytest-snapshot
RUN apt-get -y update
RUN apt install -y libsm6 \
                libxext6 \
                ffmpeg \
                libfontconfig1 \
                libxrender1 \
                libgl1-mesa-glx \
                libgeos-dev \
                gcc

WORKDIR /usr/src/
COPY requirements.txt /usr/src/
RUN pip install -r requirements.txt
COPY . /usr/src/

RUN python setup.py install
