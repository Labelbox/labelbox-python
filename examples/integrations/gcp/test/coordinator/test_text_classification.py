import requests
import hmac
import hashlib
import json
"""
This script simulates a webhook event.

# Make sure that the LABELBOX_API_KEY cooresponds to the org that belongs to this project.
# If you want any real data to be produced, there should be some bounding boes in the project.
"""
model_run_id = "9da8d98f-cf94-0517-2bc9-c107cb4ddfca"
secret = b'test_secret'

payload = json.dumps({
    'modelRunId': model_run_id,
    'modelType': 'text_single_classification'
})
signature = "sha1=" + hmac.new(
    secret, msg=payload.encode(), digestmod=hashlib.sha1).hexdigest()
res = requests.post("http://localhost:8000/model_run",
                    data=payload,
                    headers={'X-Hub-Signature': signature})
