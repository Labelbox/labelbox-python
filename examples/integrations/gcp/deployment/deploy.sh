set -e

# Force user to deliberately set google project to prevent any accidents
if [[ -z "${GOOGLE_PROJECT}" ]]; then
  echo "Must set GOOGLE_PROJECT env var."
fi

# Make sure the right project is being used
gcloud config set project $GOOGLE_PROJECT

if [[ -z "${DEPLOYMENT_NAME}" ]]; then
  echo "Must set deployment name."
elif [[ ! -z $(gcloud compute instances list | awk '/'$DEPLOYMENT_NAME'/ {print $5}') ]]; then
  echo "Deployment already exists."
  exit 0
fi

# Rollback changes if command fails..
function cleanup {
  if [ ! $? -eq 0 ]; then
      echo "Deployment failed. Cleaning up resources.."
      ./deployment/teardown.sh
  fi
}
trap cleanup EXIT

TARGET_TAGS=$DEPLOYMENT_NAME-tags
FIREWALL_NAME=$DEPLOYMENT_NAME-firewall
STATIC_IP_NAME=$DEPLOYMENT_NAME-static-ip

# TODO: Wait until done..

enable_service() {
  echo "Enabling service: $1"
  gcloud services enable $1
  for i in {1..20}; do
     sleep $i
     if gcloud services list | grep $1; then
         echo "Enabled Service: $1"
         return
     fi
  done
  echo "Failed to enable service: $1. Exiting."
  exit 1
}

# Enable vertex, GCR, cloud storage, secret manager
enable_service aiplatform.googleapis.com
enable_service containerregistry.googleapis.com
enable_service secretmanager.googleapis.com
# Not sure which (or both) is necessary..
#storage-component.googleapis.com                                                                     Cloud Storage
#storage.googleapis.com                                                                               Cloud Storage API
enable_service storage.googleapis.com

# Load secrets

# Build Containers
docker-compose build
docker-compose push

# Configure storage and secrets
docker-compose up deployment_config

# Create Ingress
gcloud compute firewall-rules create $FIREWALL_NAME \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags $TARGET_TAGS \
    --description "Allow port 8000 access to http-server"

# Create Static IP Address
gcloud compute addresses create $STATIC_IP_NAME \
    --region=us-central1
IP_ADDRESS=$(gcloud compute addresses describe $STATIC_IP_NAME --region=us-central1 --format="value(address)")


# Launch coordinator to VM
gcloud compute instances \
    create-with-container $DEPLOYMENT_NAME \
    --zone us-central1-a \
    --tags $TARGET_TAGS \
    --container-image gcr.io/${GOOGLE_PROJECT}/${DEPLOYMENT_NAME}/coordinator \
    --service-account ${GOOGLE_SERVICE_ACCOUNT} \
    --scopes "https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/devstorage.read_write" \
    --address=$IP_ADDRESS

echo "View deployment here: https://console.cloud.google.com/compute/instances?project=${GOOGLE_PROJECT}"

ENDPOINT=http://$IP_ADDRESS:8000

echo "Waiting for endpoint to become available."
for i in {1..20}
do
    sleep $i
    RESPONSE=$(curl -s --max-time 1 $ENDPOINT/ping || echo "")
    if [[ ! -z $RESPONSE ]]; then
       echo "Deployment Successful."
       echo "Service exposed on endpoint: $ENDPOINT"
       break
    fi
done


# Resport if response is empty then the service wasn't deployed properly
if [[ -z $RESPONSE ]]; then
    echo "Service unavailable."
    exit 0
fi



