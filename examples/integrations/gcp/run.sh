docker-compose build --build-arg gcs_bucket=${GCS_BUCKET}
# Push to gcr
docker-compose push
docker-compose up -d coordinator
docker-compose logs --follow coordinator
