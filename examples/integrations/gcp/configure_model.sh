docker build src/ -t coordinator
docker run -v ~/.config/gcloud:/root/.config/gcloud -p 8000:8000 coordinator bounding_box

# TODO: Add gcr config.. for pushing to gcr.. and option for doing so.
