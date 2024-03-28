#https://stackoverflow.com/questions/77364550/attributeerror-module-pkgutil-has-no-attribute-impimporter-did-you-mean
#https://github.com/pyproj4/pyproj/issues/1321
FROM python:3.8-slim-bullseye

RUN pip install pytest=="7.4.4" pytest-cases pytest-rerunfailures pytest-snapshot tox mypy strenum
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
CMD tox -e py -- tests/integration tests/data