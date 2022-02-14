## Example custom job with secrets

This container runs a script that grabs a Labelbox API key from the GCP Secrets Manager, then lists the projects in that org into a file in a bucket.

To run:

export PROJECT_ID=$(gcloud config list project --format "value(core.project)")
export IMAGE_REPO_NAME=custom_container_test
export IMAGE_TAG=test1
export IMAGE_URI=gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME:$IMAGE_TAG
export ADC=~/.config/gcloud/application_default_credentials.json


Build the container:
docker build -f Dockerfile -t $IMAGE_URI ./

Run locally:
docker run -e GCLOUD_PROJECT=sandbox-5500 -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/creds.json -v ${ADC}:/tmp/keys/creds.json:ro $IMAGE_URI --output-dir $BUCKET_NAME --secret-name XXXX

Upload to artifact registry:
docker push ${IMAGE_URI}

Run as a Vertex custom job:
- Edit config.yaml file to add container URI, secret name and bucket name

gcloud ai custom-jobs create --service-account=<service acct email to run as> --region=us-central1   --display-name=<some name> --config=config.yaml

(note you need the name of the secret as stored in gcs secret manager)

The container's logs are visible in the GCP console with the Logs Explorer.

It's also possible to have a container talk to a Tensor Board resource:
https://cloud.google.com/vertex-ai/docs/reference/rest/v1/CustomJobSpec
