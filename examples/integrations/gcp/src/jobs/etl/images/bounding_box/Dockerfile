FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
# Headless version so we don't need rendering libs
RUN pip install opencv-python-headless
ENTRYPOINT [ "python3", "bounding_box_etl.py"]
