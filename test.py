from json import tool
from xml.etree.ElementInclude import include
from labelbox import Client, Project
import time
from labelbox.data.serialization import NDJsonConverter, LBV1Converter
import os
import requests
from datetime import datetime, timezone
from pprint import pprint
from labelbox.orm.db_object import experimental
from labelbox.schema.data_row import DataRow

from labelbox.schema.data_row_metadata import (
    DataRowMetadata,
    DataRowMetadataField,
    DeleteDataRowMetadata,
)

import uuid
# import re
import json
from dataclasses import dataclass, field
from labelbox import Tool, Classification
from typing import List

from labelbox.schema.ontology import OntologyBuilder

from labelbox.schema.annotation_import import LabelImport
# from labelbox.schema.bulk_import_request import DataRow
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.ontology import Classification, OntologyBuilder, Ontology, Tool, Option
from labelbox import Label

# from labelbox.data.annotation_types.classification import ClassificationAnswer, Dropdown, Text, Radio
# from labelbox.data.metrics.confusion_matrix import feature_confusion_matrix_metric, confusion_matrix_metric
# from labelbox.data.annotation_types import ObjectAnnotation, ClassificationAnnotation, TextEntity, Mask
# import numpy as np
# from labelbox.data.serialization.labelbox_v1.label import LBV1LabelAnnotationsVideo

import logging
# logging.basicConfig(level=logging.DEBUG)


# __________________________________________
def cleanup_my_org():
    from datetime import datetime, timezone

    date = datetime.strptime("2022-06-01",
                             "%Y-%m-%d").replace(tzinfo=timezone.utc)

    for project in client.get_projects():
        if project.created_at > date:
            print(project.name)
            project.delete()
    for dataset in client.get_datasets():
        if dataset.created_at > date:
            print(dataset.name)
            dataset.delete()
    for model in client.get_models():
        model.delete()


os.system('clear')

# API_KEY = os.environ.get('apikey')
# client = Client(API_KEY, enable_experimental=True)


# API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbDN1OXJ3NzIwMDlvMHl4a2ViOHhkdml0Iiwib3JnYW5pemF0aW9uSWQiOiJjbDN1OXJ3Nm4wMDluMHl4azYzczVnNjZwIiwiYXBpS2V5SWQiOiJjbDU4YWhsaHEwYzR0MHkxZjhsYzc4NWxzIiwic2VjcmV0IjoiZTdlZjg5NTE2YjExNjQ5ZDE2MGQ1MTQxMGU1ZGUwYzIiLCJpYXQiOjE2NTcwMzI3MDQsImV4cCI6MjI4ODE4NDcwNH0.uQeS5xWVokFx5qQb-IXEgTnYnDfg_sH3jGUNd5Mw8Zc"
# client = Client(API_KEY, endpoint="https://api.lb-stage.xyz/graphql")

# print(client.get_organization())

#Python SDK Staging API Key 2




API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbDI5M2N2OWUwMDBicnRvdTBneWgyZ3RvIiwib3JnYW5pemF0aW9uSWQiOiJjbDI5M2N2NjAwMDBhcnRvdTl0M3JhMGpzIiwiYXBpS2V5SWQiOiJjbDN2c21icWgwMDBhbjdvdWFldWMwMmcyIiwic2VjcmV0IjoiYTQ4MmZjODU4OGU5YmI0NmJhZDU2YjljZDBhZDcyZTUiLCJpYXQiOjE2NTQxMDAzMTUsImV4cCI6MjI4NTI1MjMxNX0.UJC2uF8Cu6WwBSIZGUZUY8UznP7RCRsG4ns616OFXjI"
client = Client(API_KEY, endpoint='http://localhost:8080/graphql')

# API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbDN1OXJ3NzIwMDlvMHl4a2ViOHhkdml0Iiwib3JnYW5pemF0aW9uSWQiOiJjbDN1OXJ3Nm4wMDluMHl4azYzczVnNjZwIiwiYXBpS2V5SWQiOiJjbDUxZWxxd3EwMGphMHl3MTZpMWdhdmdyIiwic2VjcmV0IjoiOWFlN2E1MjhiM2JkNjY2N2ZiNThhNTU4NzMwYzc3MjYiLCJpYXQiOjE2NTY2MTYzNTMsImV4cCI6MjI4Nzc2ODM1M30.Ej8Gk01QSpAV-55UEUIxiKV5Glu1uu_BryOQwBxc9HM"
# client = Client(API_KEY, endpoint="https://api.lb-stage.xyz/graphql")

start = time.time()
project = client.get_project("cl5cwcz57000ae2ou1aoi9gld") #test queued data rows
# rows = project.export_queued_data_rows(include_metadata=True)

# dataset = client.get_dataset("cl3w2r147000qj6ou307h4045")
# rows = dataset.export_data_rows(include_metadata=True)

# project.update(queue_mode=Project.QueueMode.Batch)
# batch_rows = [row['id'] for row in project.export_queued_data_rows()][:5000]
# batch = project.create_batch(name="hello world", data_rows=batch_rows)
# print(batch.uid)
batch = list(project.batches())[0]
# rows = batch.export_data_rows(include_metadata=True)
rows = batch.export_data_rows()
#batch id is ae4dbe30-03c3-11ed-8a4d-870387097bd0

end = time.time()
print(f"{end-start} seconds")
# print(labels[-1])
count = 0
MAXIMUM = 5
for row in rows:
    # print(row.media_attributes, "\t\t", row.metadata, "\n")
    print(row,"\n")
    count +=1
    if count > MAXIMUM:
        break
# Label.bulk_delete([label for label in project.labels()])
    



# [print(f"""\n
#     {label['Media Attributes']}, 
#     {label['DataRow ID']},
#     {label['DataRow Metadata']}
#     """) for label in labels]
# bbox = [0,1,2,3]
# annotations = []

# for datarow in project.export_queued_data_rows():    
#     annotations.append({
#         "uuid": str(uuid.uuid4()),
#         "name": "bbox",
#         "dataRow": {
#             "id": datarow['id']
#         },
#         "bbox": {
#                     "left": bbox[0],
#                     "top": bbox[1],
#                     "height": bbox[2],
#                     "width": bbox[3]
#                 }
#     })

# import_annotations = LabelImport.create_from_objects(client=client, project_id = project.uid, name=f"import {str(uuid.uuid4())}", labels=annotations)
# import_annotations.wait_until_done()
# print("\nthis is complete")



# ____________________________________________________________________________________

# editor = next(client.get_labeling_frontends(where = LabelingFrontend.name == 'editor'))


# alt = {
#  "tools": [
#   {
#    "tool": "polygon",
#    "name": "jyjyjyy33",
#    "color": "#1CE6FF",
#    "label": "pgon",
#    "classifications": []
#   },
#   {
#    "tool": "rectangle",
#    "name": "jyjyjyy33",
#    "color": "#FF34FF",
#    "label": "bbox",
#    "classifications": [
#     {
#      "type": "radio",
#      "name": "radio_sub",
#      "instructions": "radio sub",
#      "options": [
#       {
#        "value": "ans_1",
#        "label": "ans 1",
#        "options": []
#       },
#       {
#        "value": "ans_12",
#        "label": "ans 12",
#        "options": []
#       }
#      ]
#     },
#     {
#      "type": "text",
#      "name": "text_sub",
#      "instructions": "text sub",
#      "uiMode": "hotkey",
#      "options": []
#     }
#    ]
#   },
#   {
#    "tool": "polygon",
#    "name": "pgon",
#    "color": "#FF4A46",
#    "label": "pgon",
#    "classifications": []
#   }
#  ],
#  "relationships": [],
#  "classifications": [
#   {
#    "type": "text",
#    "name": "bbox",
#    "instructions": "bbox",
#    "uiMode": "hotkey",
#    "scope": "global",
#    "options": []
#   }
#  ],
# }
# project.setup(editor, alt)




