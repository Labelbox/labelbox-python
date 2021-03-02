FROM python:3.7

COPY . /usr/src/labelbox
WORKDIR /usr/src/labelbox

RUN pip install pytest
RUN python setup.py install
