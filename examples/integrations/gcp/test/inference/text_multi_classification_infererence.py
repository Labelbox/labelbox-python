from google.cloud import aiplatform
import numpy as np

endpoint_name = "text_multi_classification_2022-02-15_14:09:04.205012_endpoint"
endpoint = aiplatform.Endpoint.list(filter=f'display_name="{endpoint_name}"')[0]
text = "What countries have the highest ratio of universisty students?"
result = endpoint.predict(instances=[{
    'content': text
}],
                          parameters={'confidenceThreshold': 0.5})

for prediction in result.predictions:
    names = prediction['displayNames']
    scores = prediction['confidences']
    for name, score in zip(names, scores):
        if score > 0.2:
            print(name, f"{round(100*score, 2)}%")
