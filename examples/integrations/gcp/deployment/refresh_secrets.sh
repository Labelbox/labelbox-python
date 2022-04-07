# Updates the labelbox api key and service secrets
# Will update to use whatever is currently set in your env vars


if [[ -z "${DEPLOYMENT_NAME}" ]]; then
  echo "Must set deployment name."
  exit 0
fi

echo "WARNING THIS WILL TEMPORARILY STOP YOUR SERVICE AND KILL ALL EXISTING TRAINING JOBS."
echo "DO YOU WANT TO PROCEED?"
read -p "DO YOU WANT TO PROCEED (y/N)?" -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    gcloud -q secrets delete ${DEPLOYMENT_NAME}_service_secret
    gcloud -q secrets delete ${DEPLOYMENT_NAME}_labelbox_api_key
    docker-compose up deployment_config
    gcloud -q compute instances stop --zone=us-central1-a $DEPLOYMENT_NAME
    gcloud -q compute instances start --zone=us-central1-a $DEPLOYMENT_NAME
    DEPLOYMENT_IP=$(gcloud compute instances describe $DEPLOYMENT_NAME --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    ENDPOINT=http://$DEPLOYMENT_IP:8000/ping
    echo "Waiting for endpoint to become available."
    for i in {1..20}
    do
        sleep $i
        RESPONSE=$(curl -s --max-time 1 $ENDPOINT/ping || echo "")
        if [[ ! -z $RESPONSE ]]; then
          echo "Reloaded secrets."
          exit 0
        fi
    done
    echo "Unable to connect to instance after reloading"
fi

