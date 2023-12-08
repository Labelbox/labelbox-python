import labelbox as lb
import pytest
from labelbox.schema.foundry.app import App

from labelbox.schema.foundry.foundry_client import FoundryClient

# Yolo object detection model id
TEST_MODEL_ID = "e8b352ce-8f3a-4cd6-93a5-8af904307346"


@pytest.fixture()
def random_str(rand_gen):
    return rand_gen(str)


@pytest.fixture(scope="module")
def foundry_client(client):
    return FoundryClient(client)


@pytest.fixture()
def ontology(client, random_str):
    object_features = [
        lb.Tool(tool=lb.Tool.Type.BBOX,
                name="text",
                color="#ff0000",
                classifications=[
                    lb.Classification(class_type=lb.Classification.Type.TEXT,
                                      name="value")
                ])
    ]

    ontology_builder = lb.OntologyBuilder(tools=object_features,)

    ontology = client.create_ontology(
        f"Test ontology for tesseract model {random_str}",
        ontology_builder.asdict(),
        media_type=lb.MediaType.Image)
    return ontology


@pytest.fixture()
def unsaved_app(random_str, ontology):
    return App(model_id=TEST_MODEL_ID,
               name=f"Test App {random_str}",
               description="Test App Description",
               inference_params={"confidence": 0.2},
               class_to_schema_id={},
               ontology_id=ontology.uid)


@pytest.fixture()
def app(foundry_client, unsaved_app):
    app = foundry_client._create_app(unsaved_app)
    yield app
    foundry_client._delete_app(app.id)


def test_create_app(foundry_client, unsaved_app):
    app = foundry_client._create_app(unsaved_app)
    retrieved_dict = app.dict(exclude={'id', 'created_by'})
    expected_dict = app.dict(exclude={'id', 'created_by'})
    assert retrieved_dict == expected_dict


def test_get_app(foundry_client, app):
    retrieved_app = foundry_client._get_app(app.id)
    retrieved_dict = retrieved_app.dict(exclude={'created_by'})
    expected_dict = app.dict(exclude={'created_by'})
    assert retrieved_dict == expected_dict


def test_get_app_with_invalid_id(foundry_client):
    with pytest.raises(lb.exceptions.ResourceNotFoundError):
        foundry_client._get_app("invalid-id")


def test_run_foundry_app_with_data_row_id(foundry_client, data_row, app,
                                          random_str):
    data_rows = lb.DataRowIds([data_row.uid])
    task = foundry_client.run_app(
        model_run_name=f"test-app-with-datarow-id-{random_str}",
        data_rows=data_rows,
        app_id=app.id)
    task.wait_till_done()
    assert task.status == 'COMPLETE'


def test_run_foundry_app_with_global_key(foundry_client, data_row, app,
                                         random_str):
    data_rows = lb.GlobalKeys([data_row.global_key])
    task = foundry_client.run_app(
        model_run_name=f"test-app-with-global-key-{random_str}",
        data_rows=data_rows,
        app_id=app.id)
    task.wait_till_done()
    assert task.status == 'COMPLETE'


def test_run_foundry_app_returns_model_run_id(foundry_client, data_row, app):
    data_rows = lb.GlobalKeys([data_row.global_key])
    task = foundry_client.run_app(
        model_run_name=f"test-app-with-global-key-{random_str}",
        data_rows=data_rows,
        app_id=app.id)
    model_run_id = task.metadata['modelRunId']
    model_run = foundry_client.client.get_model_run(model_run_id)
    assert model_run.uid == model_run_id


def test_run_foundry_app_with_non_existent_data_rows(foundry_client, data_row,
                                                     app, random_str):
    data_rows = lb.GlobalKeys([data_row.global_key, "non-existent-global-key"])
    task = foundry_client.run_app(
        model_run_name=f"test-app-with-wrong-key-{random_str}",
        data_rows=data_rows,
        app_id=app.id)
    task.wait_till_done()
    # The incorrect data row is filtered out and the task still completes with the correct data row
    assert task.status == 'COMPLETE'
