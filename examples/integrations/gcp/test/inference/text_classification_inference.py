from google.cloud import aiplatform
import numpy as np

endpoint_name = "text-classification_endpoint"
endpoint = aiplatform.Endpoint.list(filter=f'display_name="{endpoint_name}"')[0]
text = "I love going to the movies!"
result = endpoint.predict(instances=[{'content': text}])
prediction = result.predictions[0]
names = prediction['displayNames']
scores = prediction['confidences']
print(
    f"Sentiment is predicted as `{names[np.argmax(scores)]}` with a score of {round(100*max(scores), 2)}%"
)
