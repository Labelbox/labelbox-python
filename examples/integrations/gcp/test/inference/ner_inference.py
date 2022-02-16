from google.cloud import aiplatform

endpoint_name = "ner_2022-02-15_00:37:46.474382_endpoint"
endpoint = aiplatform.Endpoint.list(filter=f'display_name="{endpoint_name}"')[0]
text = "John told me that the weather in California is fantastic."
result = endpoint.predict(instances=[{'content': text}])
prediction_fields = [
    'textSegmentStartOffsets', 'textSegmentEndOffsets', 'confidences',
    'displayNames'
]
for prediction in result.predictions:
    for start, end, score, name in zip(
            *[prediction[k] for k in prediction_fields]):
        print(
            f"Identified `{name}` for text `{text[int(start):int(end)]}` with a score of {round(score*100, 2)}%"
        )
