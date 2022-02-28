set -e


# Load secrets
python3 create_secrets.py


# Build containers
docker-compose build
docker-compose push

# Create ingress
gcloud compute firewall-rules create default-allow-http-8000 \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags labelbox-coordinator \
    --description "Allow port 8000 access to http-server"

# Launch coordinator to VM
gcloud beta compute instances \
    create-with-container labelbox-coordinator \
    --zone us-central1-a \
    --tags labelbox-coordinator \
    --container-image gcr.io/${GOOGLE_PROJECT}/training-repo/coordinator \
    --service-account ${GOOGLE_SERVICE_ACCOUNT} \
    --scopes "https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/devstorage.read_write"

echo "View deployment here: https://console.cloud.google.com/compute/instances?project=${GOOGLE_PROJECT}"
