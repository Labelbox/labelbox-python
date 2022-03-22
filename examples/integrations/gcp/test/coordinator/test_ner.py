import requests
import hmac
import hashlib
import json
"""
This script simulates a webhook event.

# Make sure that the LABELBOX_API_KEY cooresponds to the org that belongs to this project.
# If you want any real data to be produced, there should be some text in the project.
"""
model_run_id = "9da8f643-11ea-0de5-67cf-6d9e33bb03be"
secret = b'test_secret'

payload = json.dumps({'modelRunId': model_run_id, 'modelType': 'ner'})
signature = "sha1=" + hmac.new(
    secret, msg=payload.encode(), digestmod=hashlib.sha1).hexdigest()
res = requests.post("http://localhost:8000/model_run",
                    data=payload,
                    headers={'X-Hub-Signature': signature})
