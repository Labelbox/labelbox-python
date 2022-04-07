
if [[ -z "${DEPLOYMENT_NAME}" ]]; then
  echo "Must set deployment name."
  exit 0
fi

echo "WARNING: This will temporarily stop your service and you will lose any existing training jobs."
read -p "Do you want to proceed? (y/N)" -n 1 -r

if [[ $REPLY =~ ^[Yy]$ ]]
then
    docker-compose build coordinator
    docker-compose push coordinator
    gcloud compute instances stop $DEPLOYMENT_NAME
    gcloud compute instances start $DEPLOYMENT_NAME

    DEPLOYMENT_IP=$(gcloud compute instances describe $DEPLOYMENT_NAME --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    ENDPOINT=http://$DEPLOYMENT_IP:8000/ping
    echo "Waiting for endpoint to become available."
    for i in {1..20}
    do
        sleep $i
        RESPONSE=$(curl -s --max-time 1 $ENDPOINT/ping || echo "")
        if [[ ! -z $RESPONSE ]]; then
          echo "Reloaded coordinator."
          exit 0
        fi
    done
    echo "Unable to connect to instance after reloading"
fi
