#pip install google-cloud-secret-manager

from google.cloud import secretmanager
from google.api_core.exceptions import NotFound
import os

client = secretmanager.SecretManagerServiceClient()

project_id = os.environ['GOOGLE_PROJECT']

# Any additional secrets needed to run your pipelines can be set here:

secret_ids = {
    "webhook_secret": os.environ['WEBHOOK_SECRET'],
    "labelbox_api_key": os.environ["LABELBOX_API_KEY"]
}

parent = f"projects/{project_id}"
for secret_id, secret in secret_ids.items():
    # If the secre exists, continue
    name = f"projects/{project_id}/secrets/{secret_id}/versions/1"
    try:
        client.access_secret_version(request={"name": name})
    except NotFound:
        print(f"Writing secret `{secret_id}``.")
    else:
        print(f"Secret `{secret_id}`` already exists. Skipping.")
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
