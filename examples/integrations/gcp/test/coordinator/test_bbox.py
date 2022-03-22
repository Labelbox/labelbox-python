import requests
import hmac
import hashlib
import json
"""
This script simulates a webhook event.

# Make sure that the LABELBOX_API_KEY cooresponds to the org that belongs to this project.
# If you want any real data to be produced, there should be some bounding boxes in the project.
"""
model_run_id = "9da6c7e2-bc0d-0679-1e2e-a6a4e28475c8"
secret = b'test_secret'

payload = json.dumps({'modelRunId': model_run_id, 'modelType': 'bounding_box'})
signature = "sha1=" + hmac.new(
    secret, msg=payload.encode(), digestmod=hashlib.sha1).hexdigest()
res = requests.post("http://localhost:8000/model_run",
                    data=payload,
                    headers={'X-Hub-Signature': signature})
