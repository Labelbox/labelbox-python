gcloud -q compute instances delete labelbox-coordinator --zone us-central1-a && \
gcloud -q compute firewall-rules delete default-allow-http-8000

