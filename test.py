import base64
import time
import os
from datetime import datetime, timezone
import uuid
import json
import logging
# import cuid
import random
from pprint import pprint

import requests

from labelbox import Client, Project, DataRow, Label
from labelbox.data.serialization.labelbox_v1 import LBV1Converter
from labelbox.schema.annotation_import import LabelImport, MALPredictionImport
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.ontology import Classification, OntologyBuilder, Ontology, Tool, Option

# logging.basicConfig(level=logging.DEBUG)

# ____________________________________________________________________________________
"""HELPER FUNCTIONS"""


def cleanup_my_org():
    from datetime import datetime, timezone
    date = datetime.strptime("2022-07-15",
                             "%Y-%m-%d").replace(tzinfo=timezone.utc)

    for project in client.get_projects():
        if project.created_at > date:
            print(project.name)
            project.delete()
    for dataset in client.get_datasets():
        if dataset.created_at > date:
            print(dataset.name)
            dataset.delete()
    # for model in client.get_models():
    # model.delete()


def get_lb_client(environment: str = "prod"):
    if environment == "prod":
        API_KEY = os.environ.get('apikey')
        client = Client(API_KEY)
    elif environment == "staging":
        API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbDN1OXJ3NzIwMDlvMHl4a2ViOHhkdml0Iiwib3JnYW5pemF0aW9uSWQiOiJjbDN1OXJ3Nm4wMDluMHl4azYzczVnNjZwIiwiYXBpS2V5SWQiOiJjbDZldGg2Zm0wZnBtMHkxZWJpazY2bTVlIiwic2VjcmV0IjoiYjhmNjcwZTFkYjdkODNhYzdkYzYzYjQzMjE5MTBkODQiLCJpYXQiOjE2NTk2MDQxNzYsImV4cCI6MjI5MDc1NjE3Nn0.zCYnfXQEQl8PwsJbsBvP3s_cDA-hQbiFcNgIy82uOrQ"
        client = Client(API_KEY, endpoint="https://api.lb-stage.xyz/graphql")
    elif environment == "local":
        API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbDI5M2N2OWUwMDBicnRvdTBneWgyZ3RvIiwib3JnYW5pemF0aW9uSWQiOiJjbDI5M2N2NjAwMDBhcnRvdTl0M3JhMGpzIiwiYXBpS2V5SWQiOiJjbDN2c21icWgwMDBhbjdvdWFldWMwMmcyIiwic2VjcmV0IjoiYTQ4MmZjODU4OGU5YmI0NmJhZDU2YjljZDBhZDcyZTUiLCJpYXQiOjE2NTQxMDAzMTUsImV4cCI6MjI4NTI1MjMxNX0.UJC2uF8Cu6WwBSIZGUZUY8UznP7RCRsG4ns616OFXjI"
        client = Client(API_KEY, endpoint='http://localhost:8080/graphql')
    else:
        print("Invalid environment")
        exit(1)
    return client


# ____________________________________________________________________________________

os.system('clear')

client = get_lb_client("prod")

# ____________________________________________________________________________________

project = client.get_project("cl6xntneb7t28072bggdydv7a")
# organization_id = client.get_organization().uid
# dataset = client.create_dataset(name="hello world")
# dataset = client.get_dataset("cl6xy8bcw0g7v07068u9t5hiv")
# print(dataset.uid)
# file_path = "/Users/jonathantso/Downloads/sample_batch.txt"
# dataset.create_data_rows(file_path)
# ____________________________________________________________________________________
# annotations = []

# rows = list(project.batches())[0].export_data_rows()

# for row in project.export_queued_data_rows(include_metadata=True):
#     print(f"row: {row['id']}, {row['externalId']}")
#     for i in range(4):
#         annotations.append({
#             "uuid": str(uuid.uuid4()),
#             "name": "boxy",
#             "dataRow": {"id": row['id']},
#             "bbox": {"top": round(random.uniform(0,300),2), "left": round(random.uniform(0,300),2), "height": round(random.uniform(200,500),2), "width": round(random.uniform(0,200),2)},
#             "unit": "POINTS",
#             "page": random.randint(0,9)
#         })

# import_annotations = MALPredictionImport.create_from_objects(client=client, project_id = project.uid, name=f"import {str(uuid.uuid4())}", predictions=annotations)
# import_annotations.wait_until_done()

# print(f"\nerrors: {import_annotations.errors}")
#assert should be that import_annotations.errors == []
#____________________________________________________________________________________
# labels = project.label_generator()
with open("/Users/jonathantso/Downloads/export-2022-08-17T18_37_30.233Z.json",
          "r") as f:
    labels = json.load(f)
    print("\nnow deserializing..\n")
    labels = LBV1Converter.deserialize(labels)
    # for label in labels:
    #     if label.annotations:
    #         for obj in label.annotations:
    #             print(f"\n\t{obj}")

    print("\nnow serializing..\n")
    labels = LBV1Converter.serialize(labels)
    # for label in labels:
    #     print("serialized")
    #     print(label, "\n")
    labels = LBV1Converter.deserialize(labels)
    for label in labels:
        if label.annotations:
            for obj in label.annotations:
                print(f"\n\t{obj}")
