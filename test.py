from labelbox import Client
import os
from labelbox.schema.annotation_import import MEAPredictionImport
from labelbox.schema.annotation_import import MALPredictionImport
from labelbox.schema.annotation_import import LabelImport
client = Client(api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJja3RxcTdmMjcwMDAxZ3dzYjh1b28yanduIiwib3JnYW5pemF0aW9uSWQiOiJja3RxcTdmMDkwMDAwZ3dzYmh0c2RmZmlsIiwiaWF0IjoxNjMyMDI2MTA4LCJleHAiOjE2MzI2MzA5MDh9.F4yQsuq1L-XFX4WiN9duf0s9xxpHZUn3YkMSJd4ZG1Y", endpoint="http://localhost:8080/_gql")
b = LabelImport.create_from_url(client, "ckhmkoa24001e0789rf41gm3p", "test-label-import-1",
                                 "https://storage.labelbox.com/ckk4q1vgapsau07324awnsjq2%2F388e1da0-5a2e-56b0-227f-18e452e6ac1f-1?Expires=1622247070155&KeyName=labelbox-assets-key-3&Signature=UdKsAaYAMYg0WSGZqApHoyR87Us")
# b = LabelImport.from_name(client, "ckhmkoa24001e0789rf41gm3p", "test-label-import-1")
print(b)
