FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN echo '[GoogleCompute]\nservice_account = default' > /etc/boto.cfg
ENTRYPOINT [ "python3", "bounding_box_etl.py"]
