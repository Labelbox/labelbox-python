from labelbox.schema.annotation_import import LabelImport, MEAPredictionImport
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.ontology import Classification, OntologyBuilder, Option
import tensorflow_datasets as tfds
from PIL import Image
from io import BytesIO
from labelbox import Client
from tqdm import tqdm
import uuid
from uuid import uuid4

client = Client()

CLASS_MAPPINGS = {0: 'negative', 1: 'positive'}


def setup_project(client):
    project = client.create_project(name="text_single_classification_project")
    dataset = client.create_dataset(name="text_single_classification_dataset")
    ontology_builder = OntologyBuilder(classifications=[
        Classification(Classification.Type.RADIO,
                       "positive or negative",
                       options=[Option("positive"),
                                Option("negative")]),
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


ds = tfds.load('imdb_reviews', split='train')
labels = {}
data_row_args = []
project, dataset, feature_schema_lookup = setup_project(client)
for idx, example in tqdm(enumerate(ds.as_numpy_iterator())):
    external_id = str(uuid4())
    data_row_args.append({
        'row_data': example['text'].decode('utf8'),
        'external_id': external_id
    })
    labels[external_id] = {
        "uuid": str(uuid.uuid4()),
        "schemaId": feature_schema_lookup['classification'],
        "dataRow": {
            "id": None
        },
        "answer": {
            "schemaId":
                feature_schema_lookup['options']
                [CLASS_MAPPINGS[example['label']]]
        }
    }

task = dataset.create_data_rows(data_row_args)
task.wait_till_done()

for external_id, data_row_ids in tqdm(
        client.get_data_row_ids_for_external_ids(list(labels.keys())).items()):
    data = labels[external_id]
    data_row_id = data_row_ids[0]
    labels[external_id]['dataRow'] = {'id': data_row_id}

annotations = list(labels.values())

print(f"Uploading {len(annotations)} annotations.")
job = LabelImport.create_from_objects(client, project.uid, str(uuid.uuid4()),
                                      annotations)
job.wait_until_done()
print("Upload Errors:", job.errors)

lb_model = client.create_model(name=f"{project.name}-model",
                               ontology_id=project.ontology().uid)

max_labels = 2000
labels = [label.uid for label in list(project.label_generator())[:max_labels]]
lb_model_run = lb_model.create_model_run(f"0.0.0")
lb_model_run.upsert_labels(labels)
print("Successfully created Model and ModelRun")
