FROM python:3.7

RUN pip install pytest


WORKDIR /usr/src/labelbox
COPY requirements.txt /usr/src/labelbox
RUN pip install -r requirements.txt
COPY . /usr/src/labelbox


RUN python setup.py install
