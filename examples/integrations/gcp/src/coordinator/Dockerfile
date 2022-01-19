FROM python:3.9
ENV WEBHOOK_SECRET=${WEBHOOK_SECRET:-test_secret}
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "coordinator.py"]

