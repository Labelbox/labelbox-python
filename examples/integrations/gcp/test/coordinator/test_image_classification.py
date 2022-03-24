import requests
import hmac
import hashlib
import json
"""
This script simulates a webhook event.

# Make sure that the LABELBOX_API_KEY cooresponds to the org that belongs to this project.
# If you want any real data to be produced, there should be some bounding boes in the project.
"""
model_run_id = "9ddf38cc-165c-0ae0-9cc9-4c4b83665fc7"  #"9da8885e-1d6c-0fc6-765b-c05c5166a70e"
secret = b'test_secret'

payload = json.dumps({
    'modelRunId': model_run_id,
    'modelType': 'image_single_classification'
})
signature = "sha1=" + hmac.new(
    secret, msg=payload.encode(), digestmod=hashlib.sha1).hexdigest()
res = requests.post("http://localhost:8000/model_run",
                    data=payload,
                    headers={'X-Hub-Signature': signature})
