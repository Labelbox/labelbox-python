## Example custom job with secrets

This container runs a script that grabs a Labelbox API key from the GCP Secrets Manager, then lists the projects in that org into a file in a bucket.

Still some dirty stuff because I'm copying a credentials file into the container, would need to auth that the right way but that's irrelevant to the example.

To run:

export PROJECT_ID=$(gcloud config list project --format "value(core.project)")
export IMAGE_REPO_NAME=custom_container_test
export IMAGE_TAG=test1
export IMAGE_URI=gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME:$IMAGE_TAG

docker build -f Dockerfile -t $IMAGE_URI ./
docker run $IMAGE_URI --output-dir $BUCKET_NAME

