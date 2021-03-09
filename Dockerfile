FROM python:3.7

RUN pip install pytest

COPY . /usr/src/labelbox
WORKDIR /usr/src/labelbox

RUN python setup.py install
