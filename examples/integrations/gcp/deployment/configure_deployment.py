import os

from google.cloud import secretmanager
from google.cloud import storage
from google.api_core.exceptions import NotFound
from labelbox import Client

client = Client(os.environ["LABELBOX_API_KEY"])
organization = client.get_organization()
user = client.get_user()
print("---------------------------")
print("+++ Configuring Deployment +++")
print(f"Organization ID: {organization.uid}")
print(f"Organization Name: {organization.name}")
print(f"User Email : {user.email}")

bucket_name = os.environ['GCS_BUCKET']
storage_client = storage.Client()

try:
    bucket = storage_client.get_bucket(bucket_name)
    # Restrictions set by google cloud...
    # If either of these are true then just create a new bucket
    if bucket.location_type != 'region':
        raise ValueError(
            f"Bucket location type must be `region`. Provided bucket `{bucket_name}` has location type `{bucket.location}`"
        )

    if bucket.location != 'US-CENTRAL1':
        raise ValueError(
            f"Bucket must be located in US-CENTRAL-1. Provided bucket `{bucket_name}` is located in `{bucket.location}`"
        )
    print(f"Deployment will use GCS bucket: `{bucket_name}`")
except NotFound:
    print(f"Creating new bucket with name : `{bucket_name}`")
    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = "STANDARD"
    bucket.location_type = 'region'
    bucket.location = 'US-CENTRAL-1'
    new_bucket = storage_client.create_bucket(bucket)
    print(f"Created GCS bucket: `{bucket_name}`")

client = secretmanager.SecretManagerServiceClient()
project_id = os.environ['GOOGLE_PROJECT']

# Any additional secrets needed to run your pipelines can be set here:
secret_ids = {
    f"{os.environ['DEPLOYMENT_NAME']}_service_secret":
        os.environ['SERVICE_SECRET'],
    f"{os.environ['DEPLOYMENT_NAME']}_labelbox_api_key":
        os.environ["LABELBOX_API_KEY"]
}

parent = f"projects/{project_id}"
for secret_id, secret in secret_ids.items():
    # If the secre exists, continue
    name = f"projects/{project_id}/secrets/{secret_id}/versions/1"
    try:
        client.access_secret_version(request={"name": name})
    except NotFound:
        print(f"Writing secret `{secret_id}`.")
    else:
        print(f"Secret `{secret_id}` already exists. Skipping.")
        continue

    client.create_secret(
        request={
            "parent": parent,
            "secret_id": secret_id,
            "secret": {
                "replication": {
                    "automatic": {}
                }
            },
        })
    client.add_secret_version(
        request={
            "parent": client.secret_path(project_id, secret_id),
            "payload": {
                "data": "{}".format(secret).encode('utf-8')
            }
        })
