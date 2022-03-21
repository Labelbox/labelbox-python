import uuid
import json
import os
import time

from labelbox import Client, LabelingFrontend, DataRow
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.ontology import OntologyBuilder, Tool
from labelbox.data.serialization import NDJsonConverter, LBV1Converter

client = Client(os.environ.get('LABELBOX_API_KEY'))


def setup_project(client):
    """Creates a project and dataset.
    Uses assets in repository to create datarows
    """
    project = client.create_project(name="bbox_training_project")
    dataset = client.create_dataset(name="bbox_training_dataset")
    ontology = OntologyBuilder()
    ontology.add_tool(Tool(tool=Tool.Type.BBOX, name="person"))
    ontology.add_tool(Tool(tool=Tool.Type.BBOX, name="animal"))
    editor = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'editor'))
    project.setup(editor, ontology.asdict())
    project.datasets.connect(dataset)

    #fetch from gcs bucket the assets
    os.system(
        "gsutil -m cp -r gs://vertex-matt-test/bbox_seed_datarows ../assets")

    datarows = []
    assets_directory = "../assets/bbox_seed_datarows/"

    print("Assets acquired from gcs. Now creating datarows...")

    for fp in os.listdir(assets_directory):
        full_path = os.path.join(assets_directory, fp)
        datarows.append({
            DataRow.row_data: full_path,
            DataRow.external_id: full_path.split("/")[-1]
        })

    dataset.create_data_rows(datarows)
    return project, dataset


project, dataset = setup_project(client)
time.sleep(30)  #adding sleep so ensure datarows are created

with open("../assets/proj_ckq778m4g0edr0yao004l41l7_export.json") as f:
    labels = json.load(f)
    labels = LBV1Converter().deserialize(labels).as_list()

label_data_external_ids = []
for label in labels:
    annots = label.annotations
    for annotation in annots:
        annotation.feature_schema_id = None
    external_id = label.data.external_id.split("/")[-1]
    label.data.uid = dataset.data_row_for_external_id(external_id).uid

labels.assign_feature_schema_ids(OntologyBuilder().from_project(project))

annotations = list(NDJsonConverter.serialize(labels))

job = LabelImport.create_from_objects(client, project.uid, str(uuid.uuid4()),
                                      annotations)

print("Upload Errors:", job.errors)

lb_model = client.create_model(name=f"{project.name}-model",
                               ontology_id=project.ontology().uid)
lb_model_run = lb_model.create_model_run("0.0.0")
lb_model_run.upsert_labels([label.uid for label in project.label_generator()])

print("Successfully created Model and ModelRun")
