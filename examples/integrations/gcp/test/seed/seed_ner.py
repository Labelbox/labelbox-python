import uuid
from datasets import load_dataset
from labelbox import Client, LabelingFrontend
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.ontology import OntologyBuilder, Tool
from tqdm import tqdm

ENTITIES = {
    0: '[PAD]',
    1: 'B-PER',
    2: 'I-PER',
    3: 'B-ORG',
    4: 'I-ORG',
    5: 'B-LOC',
    6: 'I-LOC',
    7: 'B-MISC',
    8: 'I-MISC'
}


def setup_project(client):
    project = client.create_project(name="ner_training_project")
    dataset = client.create_dataset(name="net_training_dataset")
    ontology_builder = OntologyBuilder(tools=[
        Tool(tool=Tool.Type.NER, name=name)
        for name in list(ENTITIES.values())[1:]
    ])
    editor = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'editor'))
    project.setup(editor, ontology_builder.asdict())
    project.datasets.connect(dataset)
    feature_schema_lookup = {
        tool.name: tool.feature_schema_id
        for tool in project.ontology().tools()
    }

    return project, dataset, feature_schema_lookup


def generate_label(feature_schema_lookup, tokens, ner_tags):
    text = ""
    idx = 0
    annotations = []
    for token, ner_tag in zip(tokens, ner_tags):
        text += token + " "
        if ner_tag != 0:
            annotations.append({
                "uuid": str(uuid.uuid4()),
                "schemaId": feature_schema_lookup[ENTITIES[ner_tag]],
                "dataRow": {
                    "id": None
                },
                "location": {
                    "start": idx,
                    "end": idx + len(token) - 1
                }
            })
        idx += len(token) + 1
    return annotations, text


def create_labels(feature_schema_lookup):
    conll_data = load_dataset("conll2003")
    label_data = {}
    for tokens, ner_tags in tqdm(
            zip(conll_data['train']['tokens'],
                conll_data['train']['ner_tags'])):
        annotations, text = generate_label(feature_schema_lookup, tokens,
                                           ner_tags)
        if len(annotations):
            label_data[str(uuid.uuid4())] = {
                'text': text,
                'annotations': annotations
            }
    return label_data


def upload_to_labelbox(client, project, upload_annotations):
    print(f"Uploading {len(upload_annotations)} annotations.")
    job = LabelImport.create_from_objects(client, project.uid,
                                          str(uuid.uuid4()), upload_annotations)
    job.wait_until_done()
    print("Upload Errors:", job.errors)


def assign_data_row_ids(client, labels):
    for external_id, data_row_ids in tqdm(
            client.get_data_row_ids_for_external_ids(list(
                labels.keys())).items()):
        data = labels[external_id]['annotations']
        data_row_id = data_row_ids[0]
        for annot in data:
            annot['dataRow'] = {'id': data_row_id}


def flatten_labels(labels):
    return [
        annotation for label in labels.values()
        for annotation in label['annotations']
    ]


def main():
    client = Client()
    project, dataset, feature_schema_lookup = setup_project(client)
    labels = create_labels(feature_schema_lookup)
    task = dataset.create_data_rows([{
        'row_data': data['text'],
        'external_id': external_id
    } for external_id, data in labels.items()])
    task.wait_till_done()
    assign_data_row_ids(client, labels)
    annotations = flatten_labels(labels)
    upload_to_labelbox(client, project, annotations)

    lb_model = client.create_model(name=f"{project.name}-model",
                                   ontology_id=project.ontology().uid)

    #iterate over every 2k labels to upload
    max_labels = 2000
    labels = [
        label.uid for label in list(project.label_generator())[:max_labels]
    ]
    lb_model_run = lb_model.create_model_run(f"0.0.0")
    lb_model_run.upsert_labels(labels)

    print("Successfully created Model and ModelRun", lb_model_run.uid)


if __name__ == '__main__':
    main()
