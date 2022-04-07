FROM python:3.9
WORKDIR /app
COPY . .

RUN pip3 install google-cloud-secret-manager google-cloud-storage labelbox
ENTRYPOINT [ "python3", "configure_deployment.py"]
