docker build src/ -t coordinator
docker run -p 8000:8000 coordinator bounding_box
