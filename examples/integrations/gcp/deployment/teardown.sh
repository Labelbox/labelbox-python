

if [[ -z "${DEPLOYMENT_NAME}" ]]; then
  echo "Must set deployment name."
  exit 0
fi

TARGET_TAGS=$DEPLOYMENT_NAME-tags
FIREWALL_NAME=$DEPLOYMENT_NAME-firewall
STATIC_IP_NAME=$DEPLOYMENT_NAME-static-ip

gcloud -q secrets delete ${DEPLOYMENT_NAME}_service_secret
gcloud -q secrets delete ${DEPLOYMENT_NAME}_labelbox_api_key

gcloud -q compute instances delete $DEPLOYMENT_NAME --zone us-central1-a
gcloud -q compute firewall-rules delete $FIREWALL_NAME
gcloud -q compute addresses delete $STATIC_IP_NAME --region=us-central1


