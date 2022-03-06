from collections import defaultdict
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.ontology import Classification, OntologyBuilder, Option
import tensorflow_datasets as tfds
from PIL import Image
from io import BytesIO
from labelbox import Client
from tqdm import tqdm
import uuid

client = Client()

CLASS_MAPPINGS_COURSE = ["DESC", "ENTY", "ABBR", "HUM", "NUM", "LOC"]
CLASS_MAPPINGS_FINE = [
    "manner",
    "cremat",
    "animal",
    "exp",
    "ind",
    "gr",
    "title",
    "def",
    "date",
    "reason",
    "event",
    "state",
    "desc",
    "count",
    "other",
    "letter",
    "religion",
    "food",
    "country",
    "color",
    "termeq",
    "city",
    "body",
    "dismed",
    "mount",
    "money",
    "product",
    "period",
    "substance",
    "sport",
    "plant",
    "techmeth",
    "volsize",
    "instru",
    "abb",
    "speed",
    "word",
    "lang",
    "perc",
    "code",
    "dist",
    "temp",
    "symbol",
    "ord",
    "veh",
    "weight",
    "currency",
]


def setup_project(client):
    project = client.create_project(name="text_multi_classification_project")
    dataset = client.create_dataset(name="text_multi_classification_dataset")
    ontology_builder = OntologyBuilder(classifications=[
        Classification(Classification.Type.RADIO,
                       "fine",
                       options=[Option(name) for name in CLASS_MAPPINGS_FINE]),
        Classification(Classification.Type.RADIO,
                       "course",
                       options=[Option(name)
                                for name in CLASS_MAPPINGS_COURSE]),
    ])
    editor = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'editor'))
    project.setup(editor, ontology_builder.asdict())
    project.datasets.connect(dataset)
    classification = project.ontology().classifications()
    feature_schema_lookup = {
        classification[0].name: classification[0].feature_schema_id,
        classification[1].name: classification[1].feature_schema_id,
        f'{classification[0].name}-options': {
            option.value: option.feature_schema_id
            for option in classification[0].options
        },
        f'{classification[1].name}-options': {
            option.value: option.feature_schema_id
            for option in classification[1].options
        }
    }
    return project, dataset, feature_schema_lookup


ds = tfds.load('trec', split='train')
labels = defaultdict(list)
project, dataset, feature_schema_lookup = setup_project(client)
data_row_data = []
for idx, example in tqdm(enumerate(ds.as_numpy_iterator())):
    fine_class_name, course_class_name = example['label-fine'], example[
        'label-coarse']
    external_id = str(uuid.uuid4())
    data_row_data.append({
        'external_id': external_id,
        'row_data': example['text'].decode('utf8')
    })
    labels[external_id].extend([{
        "uuid": str(uuid.uuid4()),
        "schemaId": feature_schema_lookup['fine'],
        "dataRow": {
            "id": external_id
        },
        "answer": {
            "schemaId":
                feature_schema_lookup['fine-options']
                [CLASS_MAPPINGS_FINE[fine_class_name]]
        }
    }, {
        "uuid": str(uuid.uuid4()),
        "schemaId": feature_schema_lookup['course'],
        "dataRow": {
            "id": external_id
        },
        "answer": {
            "schemaId":
                feature_schema_lookup['course-options']
                [CLASS_MAPPINGS_COURSE[course_class_name]]
        }
    }])


def assign_data_row_ids(client, labels):
    for external_id, data_row_ids in tqdm(
            client.get_data_row_ids_for_external_ids(list(
                labels.keys())).items()):
        data = labels[external_id]
        data_row_id = data_row_ids[0]
        for annot in data:
            annot['dataRow'] = {'id': data_row_id}


def flatten_labels(labels):
    return [annotation for label in labels.values() for annotation in label]


task = dataset.create_data_rows(data_row_data)
task.wait_till_done()

assign_data_row_ids(client, labels)
annotations = flatten_labels(labels)
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
