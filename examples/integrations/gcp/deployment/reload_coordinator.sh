
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
