FROM python:3.9
RUN apt-get update -y && apt-get install -y libgl1-mesa-glx
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT [ "python3", "classification_etl.py"]
