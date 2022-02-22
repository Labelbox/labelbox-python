

gcloud compute firewall-rules create default-allow-http-80 \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server \
    --description "Allow port 8080 access to http-server"



gcloud beta compute instances \
    create-with-container test-vm \
    --zone us-central1-a \
    --tags http-server \
    --container-image gcr.io/${GOOGLE_PROJECT}/training-repo/coordinator \
    --service-account ${GOOGLE_SERVICE_ACCOUNT} \
    --scopes "https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/devstorage.read_write"

