import uuid
from io import BytesIO

from PIL import Image
from tqdm import tqdm
import tensorflow_datasets as tfds

from labelbox import Client
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.ontology import Classification, OntologyBuilder, Option

client = Client()

CLASS_MAPPINGS = {0: 'cat', 1: 'dog'}


def setup_project(client):
    project = client.create_project(name="image_single_classification_project")
    dataset = client.create_dataset(name="image_single_classification_dataset")
    ontology_builder = OntologyBuilder(classifications=[
        Classification(Classification.Type.RADIO,
                       "dog or cat",
                       options=[Option("dog"), Option("cat")]),
    ])
    editor = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'editor'))
    project.setup(editor, ontology_builder.asdict())
    project.datasets.connect(dataset)
    classification = project.ontology().classifications()[0]
    feature_schema_lookup = {
        'classification': classification.feature_schema_id,
        'options': {
            option.value: option.feature_schema_id
            for option in classification.options
        }
    }
    return project, dataset, feature_schema_lookup


ds = tfds.load('cats_vs_dogs', split='train')
annotations = []
max_examples = 350
project, dataset, feature_schema_lookup = setup_project(client)
for idx, example in tqdm(enumerate(ds.as_numpy_iterator())):
    if idx > max_examples:
        break

    im_bytes = BytesIO()
    Image.fromarray(example['image']).save(im_bytes, format="jpeg")
    uri = client.upload_data(content=im_bytes.getvalue(),
                             filename=f"{uuid.uuid4()}.jpg")
    data_row = dataset.create_data_row(row_data=uri)
    annotations.append({
        "uuid": str(uuid.uuid4()),
        "schemaId": feature_schema_lookup['classification'],
        "dataRow": {
            "id": data_row.uid
        },
        "answer": {
            "schemaId":
                feature_schema_lookup['options']
                [CLASS_MAPPINGS[example['label']]]
        }
    })

print(f"Uploading {len(annotations)} annotations.")
job = LabelImport.create_from_objects(client, project.uid, str(uuid.uuid4()),
                                      annotations)
job.wait_until_done()
print("Upload Errors:", job.errors)
