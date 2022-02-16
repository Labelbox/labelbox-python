import base64
from io import BytesIO

from google.cloud import aiplatform
from PIL import Image, ImageDraw

endpoint_name = "bounding_box_2022-02-15_00:02:17.099020_endpoint"
endpoint = aiplatform.Endpoint.list(filter=f'display_name="{endpoint_name}"')[0]

with open('dog.jpg', "rb") as f:
    image_bytes = f.read()

# Note that the max content size is 1.5mb
b64_bytes = base64.b64encode(image_bytes).decode("utf-8")
result = endpoint.predict(instances=[{
    'content': b64_bytes
}],
                          parameters={
                              'confidenceThreshold': 0.5,
                              'maxPredictions': 5
                          })

im = Image.open(BytesIO(image_bytes))
w, h = im.size
d = ImageDraw.Draw(im)
for prediction in result.predictions:
    for bbox in prediction['bboxes']:
        d.rectangle([bbox[0] * w, bbox[2] * h, bbox[1] * w, bbox[3] * h])
im.show()
