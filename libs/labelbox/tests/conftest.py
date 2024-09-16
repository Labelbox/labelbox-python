from datetime import datetime
from random import randint
from string import ascii_letters

import json
import os
import re
import uuid
import time
from labelbox.schema.project import Project
import requests
from labelbox.schema.ontology import Ontology
import pytest
from types import SimpleNamespace
from typing import Type
from enum import Enum
from typing import Tuple

from labelbox import Dataset, DataRow
from labelbox import MediaType
from labelbox.orm import query
from labelbox.pagination import PaginatedCollection
from labelbox.schema.invite import Invite
from labelbox.schema.quality_mode import QualityMode
from labelbox.schema.queue_mode import QueueMode
from labelbox import Client

from labelbox import LabelingFrontend
from labelbox import OntologyBuilder, Tool, Option, Classification
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.enums import AnnotationImportState
from labelbox.exceptions import LabelboxError

IMG_URL = "https://picsum.photos/200/300.jpg"
MASKABLE_IMG_URL = "https://storage.googleapis.com/labelbox-datasets/image_sample_data/2560px-Kitano_Street_Kobe01s5s4110.jpeg"
SMALL_DATASET_URL = "https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/potato.jpeg"
DATA_ROW_PROCESSING_WAIT_TIMEOUT_SECONDS = 30
DATA_ROW_PROCESSING_WAIT_SLEEP_INTERNAL_SECONDS = 3
EPHEMERAL_BASE_URL = "http://lb-api-public"
IMAGE_URL = "https://storage.googleapis.com/diagnostics-demo-data/coco/COCO_train2014_000000000034.jpg"
EXTERNAL_ID = "my-image"

pytest_plugins = []


@pytest.fixture(scope="session")
def rand_gen():
    def gen(field_type):
        if field_type is str:
            return "".join(
                ascii_letters[randint(0, len(ascii_letters) - 1)]
                for _ in range(16)
            )

        if field_type is datetime:
            return datetime.now()

        raise Exception(
            "Can't random generate for field type '%r'" % field_type
        )

    return gen


class Environ(Enum):
    LOCAL = "local"
    PROD = "prod"
    STAGING = "staging"
    CUSTOM = "custom"
    STAGING_EU = "staging-eu"
    EPHEMERAL = "ephemeral"  # Used for testing PRs with ephemeral environments


@pytest.fixture
def image_url() -> str:
    return MASKABLE_IMG_URL


@pytest.fixture
def external_id() -> str:
    return EXTERNAL_ID


def ephemeral_endpoint() -> str:
    return os.getenv("LABELBOX_TEST_BASE_URL", EPHEMERAL_BASE_URL)


def graphql_url(environ: str) -> str:
    if environ == Environ.LOCAL:
        return "http://localhost:3000/api/graphql"
    elif environ == Environ.PROD:
        return "https://api.labelbox.com/graphql"
    elif environ == Environ.STAGING:
        return "https://api.lb-stage.xyz/graphql"
    elif environ == Environ.CUSTOM:
        graphql_api_endpoint = os.environ.get(
            "LABELBOX_TEST_GRAPHQL_API_ENDPOINT"
        )
        if graphql_api_endpoint is None:
            raise Exception("Missing LABELBOX_TEST_GRAPHQL_API_ENDPOINT")
        return graphql_api_endpoint
    elif environ == Environ.EPHEMERAL:
        return f"{ephemeral_endpoint()}/graphql"
    return "http://host.docker.internal:8080/graphql"


def rest_url(environ: str) -> str:
    if environ == Environ.LOCAL:
        return "http://localhost:3000/api/v1"
    elif environ == Environ.PROD:
        return "https://api.labelbox.com/api/v1"
    elif environ == Environ.STAGING:
        return "https://api.lb-stage.xyz/api/v1"
    elif environ == Environ.CUSTOM:
        rest_api_endpoint = os.environ.get("LABELBOX_TEST_REST_API_ENDPOINT")
        if rest_api_endpoint is None:
            raise Exception("Missing LABELBOX_TEST_REST_API_ENDPOINT")
        return rest_api_endpoint
    elif environ == Environ.EPHEMERAL:
        return f"{ephemeral_endpoint()}/api/v1"
    return "http://host.docker.internal:8080/api/v1"


def testing_api_key(environ: Environ) -> str:
    keys = [
        f"LABELBOX_TEST_API_KEY_{environ.value.upper()}",
        "LABELBOX_TEST_API_KEY",
        "LABELBOX_API_KEY",
    ]
    for key in keys:
        value = os.environ.get(key)
        if value is not None:
            return value
    raise Exception("Cannot find API to use for tests")


def service_api_key() -> str:
    service_api_key = os.environ["SERVICE_API_KEY"]
    if service_api_key is None:
        raise Exception(
            "SERVICE_API_KEY is missing and needed for admin client"
        )
    return service_api_key


class IntegrationClient(Client):
    def __init__(self, environ: str) -> None:
        api_url = graphql_url(environ)
        api_key = testing_api_key(environ)
        rest_endpoint = rest_url(environ)
        super().__init__(
            api_key,
            api_url,
            enable_experimental=True,
            rest_endpoint=rest_endpoint,
        )
        self.queries = []

    def execute(self, query=None, params=None, check_naming=True, **kwargs):
        if check_naming and query is not None:
            assert (
                re.match(r"\s*(?:query|mutation) \w+PyApi", query) is not None
            )
        self.queries.append((query, params))
        if not kwargs.get("timeout"):
            kwargs["timeout"] = 30.0
        return super().execute(query, params, **kwargs)


class AdminClient(Client):
    def __init__(self, env):
        """
        The admin client creates organizations and users using admin api described here https://labelbox.atlassian.net/wiki/spaces/AP/pages/2206564433/Internal+Admin+APIs.
        """
        self._api_key = service_api_key()
        self._admin_endpoint = f"{ephemeral_endpoint()}/admin/v1"
        self._api_url = graphql_url(env)
        self._rest_endpoint = rest_url(env)

        super().__init__(
            self._api_key,
            self._api_url,
            enable_experimental=True,
            rest_endpoint=self._rest_endpoint,
        )

    def _create_organization(self) -> str:
        endpoint = f"{self._admin_endpoint}/organizations/"
        response = requests.post(
            endpoint,
            headers=self.headers,
            json={"name": f"Test Org {uuid.uuid4()}"},
        )

        data = response.json()
        if response.status_code not in [
            requests.codes.created,
            requests.codes.ok,
        ]:
            raise Exception(
                "Failed to create org, message: " + str(data["message"])
            )

        return data["id"]

    def _create_user(self, organization_id=None) -> Tuple[str, str]:
        if organization_id is None:
            organization_id = self.organization_id

        endpoint = f"{self._admin_endpoint}/user-identities/"
        identity_id = f"e2e+{uuid.uuid4()}"

        response = requests.post(
            endpoint,
            headers=self.headers,
            json={
                "identityId": identity_id,
                "email": "email@email.com",
                "name": f"tester{uuid.uuid4()}",
                "verificationStatus": "VERIFIED",
            },
        )
        data = response.json()
        if response.status_code not in [
            requests.codes.created,
            requests.codes.ok,
        ]:
            raise Exception(
                "Failed to create user, message: " + str(data["message"])
            )

        user_identity_id = data["identityId"]

        endpoint = (
            f"{self._admin_endpoint}/organizations/{organization_id}/users/"
        )
        response = requests.post(
            endpoint,
            headers=self.headers,
            json={"identityId": user_identity_id, "organizationRole": "Admin"},
        )

        data = response.json()
        if response.status_code not in [
            requests.codes.created,
            requests.codes.ok,
        ]:
            raise Exception(
                "Failed to create link user to org, message: "
                + str(data["message"])
            )

        user_id = data["id"]

        endpoint = f"{self._admin_endpoint}/users/{user_id}/token"
        response = requests.get(
            endpoint,
            headers=self.headers,
        )
        data = response.json()
        if response.status_code not in [
            requests.codes.created,
            requests.codes.ok,
        ]:
            raise Exception(
                "Failed to create ephemeral user, message: "
                + str(data["message"])
            )

        token = data["token"]

        return user_id, token

    def create_api_key_for_user(self) -> str:
        organization_id = self._create_organization()
        _, user_token = self._create_user(organization_id)
        key_name = f"test-key+{uuid.uuid4()}"
        query = """mutation CreateApiKeyPyApi($name: String!) {
                createApiKey(data: {name: $name}) {
                    id
                    jwt
                }
            }
        """
        params = {"name": key_name}
        self.headers["Authorization"] = f"Bearer {user_token}"
        res = self.execute(query, params, error_log_key="errors")

        return res["createApiKey"]["jwt"]


class EphemeralClient(Client):
    def __init__(self, environ=Environ.EPHEMERAL):
        self.admin_client = AdminClient(environ)
        self.api_key = self.admin_client.create_api_key_for_user()
        api_url = graphql_url(environ)
        rest_endpoint = rest_url(environ)

        super().__init__(
            self.api_key,
            api_url,
            enable_experimental=True,
            rest_endpoint=rest_endpoint,
        )


@pytest.fixture
def ephmeral_client() -> EphemeralClient:
    return EphemeralClient


@pytest.fixture
def admin_client() -> AdminClient:
    return AdminClient


@pytest.fixture
def integration_client() -> IntegrationClient:
    return IntegrationClient


@pytest.fixture(scope="session")
def environ() -> Environ:
    """
    Checks environment variables for LABELBOX_ENVIRON to be
    'prod' or 'staging'
    Make sure to set LABELBOX_TEST_ENVIRON in .github/workflows/python-package.yaml
    """
    keys = ["LABELBOX_TEST_ENV", "LABELBOX_TEST_ENVIRON", "LABELBOX_ENV"]
    for key in keys:
        value = os.environ.get(key)
        if value is not None:
            return Environ(value)
    raise Exception(f"Missing env key in: {os.environ}")


def cancel_invite(client, invite_id):
    """
    Do not use. Only for testing.
    """
    query_str = """mutation CancelInvitePyApi($where: WhereUniqueIdInput!) {
            cancelInvite(where: $where) {id}}"""
    client.execute(query_str, {"where": {"id": invite_id}}, experimental=True)


def get_project_invites(client, project_id):
    """
    Do not use. Only for testing.
    """
    id_param = "projectId"
    query_str = """query GetProjectInvitationsPyApi($from: ID, $first: PageSize, $%s: ID!) {
        project(where: {id: $%s}) {id
        invites(from: $from, first: $first) { nodes { %s
        projectInvites { projectId projectRoleName } } nextCursor}}}
    """ % (id_param, id_param, query.results_query_part(Invite))
    return PaginatedCollection(
        client,
        query_str,
        {id_param: project_id},
        ["project", "invites", "nodes"],
        Invite,
        cursor_path=["project", "invites", "nextCursor"],
    )


def get_invites(client):
    """
    Do not use. Only for testing.
    """
    query_str = """query GetOrgInvitationsPyApi($from: ID, $first: PageSize) {
            organization { id invites(from: $from, first: $first) {
                nodes { id createdAt organizationRoleName inviteeEmail } nextCursor }}}"""
    invites = PaginatedCollection(
        client,
        query_str,
        {},
        ["organization", "invites", "nodes"],
        Invite,
        cursor_path=["organization", "invites", "nextCursor"],
        experimental=True,
    )
    return invites


@pytest.fixture
def queries():
    return SimpleNamespace(
        cancel_invite=cancel_invite,
        get_project_invites=get_project_invites,
        get_invites=get_invites,
    )


@pytest.fixture(scope="session")
def admin_client(environ: str):
    return AdminClient(environ)


@pytest.fixture(scope="session")
def client(environ: str):
    if environ == Environ.EPHEMERAL:
        return EphemeralClient()
    return IntegrationClient(environ)


@pytest.fixture(scope="session")
def pdf_url(client):
    pdf_url = client.upload_file("tests/assets/loremipsum.pdf")
    return {
        "row_data": {
            "pdf_url": pdf_url,
        },
        "global_key": str(uuid.uuid4()),
    }


@pytest.fixture(scope="session")
def pdf_entity_data_row(client):
    pdf_url = client.upload_file(
        "tests/assets/arxiv-pdf_data_99-word-token-pdfs_0801.3483.pdf"
    )
    text_layer_url = client.upload_file(
        "tests/assets/arxiv-pdf_data_99-word-token-pdfs_0801.3483-lb-textlayer.json"
    )

    return {
        "row_data": {"pdf_url": pdf_url, "text_layer_url": text_layer_url},
        "global_key": str(uuid.uuid4()),
    }


@pytest.fixture()
def conversation_entity_data_row(client, rand_gen):
    return {
        "row_data": "https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json",
        "global_key": f"https://storage.googleapis.com/labelbox-developer-testing-assets/conversational_text/1000-conversations/conversation-1.json-{rand_gen(str)}",
    }


@pytest.fixture
def project(client, rand_gen):
    project = client.create_project(
        name=rand_gen(str),
        queue_mode=QueueMode.Batch,
        media_type=MediaType.Image,
    )
    yield project
    project.delete()


@pytest.fixture
def consensus_project(client, rand_gen):
    project = client.create_project(
        name=rand_gen(str),
        quality_mode=QualityMode.Consensus,
        queue_mode=QueueMode.Batch,
        media_type=MediaType.Image,
    )
    yield project
    project.delete()


@pytest.fixture
def model_config(client, rand_gen, valid_model_id):
    model_config = client.create_model_config(
        name=rand_gen(str),
        model_id=valid_model_id,
        inference_params={"param": "value"},
    )
    yield model_config
    client.delete_model_config(model_config.uid)


@pytest.fixture
def consensus_project_with_batch(
    consensus_project, initial_dataset, rand_gen, image_url
):
    project = consensus_project
    dataset = initial_dataset

    data_rows = []
    for _ in range(3):
        data_rows.append(
            {DataRow.row_data: image_url, DataRow.global_key: str(uuid.uuid4())}
        )
    task = dataset.create_data_rows(data_rows)
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 3
    batch = project.create_batch(
        rand_gen(str),
        data_rows,  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )

    yield [project, batch, data_rows]
    batch.delete()


@pytest.fixture
def dataset(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    yield dataset
    dataset.delete()


@pytest.fixture(scope="function")
def unique_dataset(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    yield dataset
    dataset.delete()


@pytest.fixture
def small_dataset(dataset: Dataset):
    task = dataset.create_data_rows(
        [
            {"row_data": SMALL_DATASET_URL, "external_id": "my-image"},
        ]
        * 2
    )
    task.wait_till_done()

    yield dataset


@pytest.fixture
def data_row(dataset, image_url, rand_gen):
    global_key = f"global-key-{rand_gen(str)}"
    task = dataset.create_data_rows(
        [
            {
                "row_data": image_url,
                "external_id": "my-image",
                "global_key": global_key,
            },
        ]
    )
    task.wait_till_done()
    dr = dataset.data_rows().get_one()
    yield dr
    dr.delete()


@pytest.fixture
def data_row_and_global_key(dataset, image_url, rand_gen):
    global_key = f"global-key-{rand_gen(str)}"
    task = dataset.create_data_rows(
        [
            {
                "row_data": image_url,
                "external_id": "my-image",
                "global_key": global_key,
            },
        ]
    )
    task.wait_till_done()
    dr = dataset.data_rows().get_one()
    yield dr, global_key
    dr.delete()


# can be used with
# @pytest.mark.parametrize('data_rows', [<count of data rows>], indirect=True)
# if omitted, count defaults to 1
@pytest.fixture
def data_rows(
    dataset, image_url, request, wait_for_data_row_processing, client
):
    count = 1
    if hasattr(request, "param"):
        count = request.param

    datarows = [
        dict(row_data=image_url, global_key=f"global-key-{uuid.uuid4()}")
        for _ in range(count)
    ]

    task = dataset.create_data_rows(datarows)
    task.wait_till_done()
    datarows = dataset.data_rows().get_many(count)
    for dr in dataset.data_rows():
        wait_for_data_row_processing(client, dr)

    yield datarows

    for datarow in datarows:
        datarow.delete()


@pytest.fixture
def iframe_url(environ) -> str:
    if environ in [Environ.PROD, Environ.LOCAL]:
        return "https://editor.labelbox.com"
    elif environ == Environ.STAGING:
        return "https://editor.lb-stage.xyz"


@pytest.fixture
def sample_image() -> str:
    path_to_video = "tests/integration/media/sample_image.jpg"
    return path_to_video


@pytest.fixture
def sample_video() -> str:
    path_to_video = "tests/integration/media/cat.mp4"
    return path_to_video


@pytest.fixture
def sample_bulk_conversation() -> list:
    path_to_conversation = "tests/integration/media/bulk_conversation.json"
    with open(path_to_conversation) as json_file:
        conversations = json.load(json_file)
    return conversations


@pytest.fixture
def organization(client):
    # Must have at least one seat open in your org to run these tests
    org = client.get_organization()

    yield org


@pytest.fixture
def configured_project_with_label(
    client,
    rand_gen,
    dataset,
    data_row,
    wait_for_label_processing,
    teardown_helpers,
):
    """Project with a connected dataset, having one datarow

    Project contains an ontology with 1 bbox tool
    Additionally includes a create_label method for any needed extra labels
    One label is already created and yielded when using fixture
    """
    project = client.create_project(
        name=rand_gen(str),
        queue_mode=QueueMode.Batch,
        media_type=MediaType.Image,
    )
    project._wait_until_data_rows_are_processed(
        data_row_ids=[data_row.uid],
        wait_processing_max_seconds=DATA_ROW_PROCESSING_WAIT_TIMEOUT_SECONDS,
        sleep_interval=DATA_ROW_PROCESSING_WAIT_SLEEP_INTERNAL_SECONDS,
    )

    project.create_batch(
        rand_gen(str),
        [data_row.uid],  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    ontology = _setup_ontology(project)
    label = _create_label(
        project, data_row, ontology, wait_for_label_processing
    )
    yield [project, dataset, data_row, label]

    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)


def _create_label(project, data_row, ontology, wait_for_label_processing):
    predictions = [
        {
            "uuid": str(uuid.uuid4()),
            "schemaId": ontology.tools[0].feature_schema_id,
            "dataRow": {"id": data_row.uid},
            "bbox": {"top": 20, "left": 20, "height": 50, "width": 50},
        }
    ]

    def create_label():
        """Ad-hoc function to create a LabelImport
        Creates a LabelImport task which will create a label
        """
        upload_task = LabelImport.create_from_objects(
            project.client,
            project.uid,
            f"label-import-{uuid.uuid4()}",
            predictions,
        )
        upload_task.wait_until_done(sleep_time_seconds=5)
        assert (
            upload_task.state == AnnotationImportState.FINISHED
        ), "Label Import did not finish"
        assert (
            len(upload_task.errors) == 0
        ), f"Label Import {upload_task.name} failed with errors {upload_task.errors}"

    project.create_label = create_label
    project.create_label()
    label = wait_for_label_processing(project)[0]
    return label


def _setup_ontology(project):
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"
        )
    )[0]
    ontology_builder = OntologyBuilder(
        tools=[
            Tool(tool=Tool.Type.BBOX, name="test-bbox-class"),
        ]
    )
    project.setup(editor, ontology_builder.asdict())
    # TODO: ontology may not be synchronous after setup. remove sleep when api is more consistent
    time.sleep(2)
    return OntologyBuilder.from_project(project)


@pytest.fixture
def big_dataset(dataset: Dataset):
    task = dataset.create_data_rows(
        [
            {"row_data": IMAGE_URL, "external_id": EXTERNAL_ID},
        ]
        * 3
    )
    task.wait_till_done()

    yield dataset


@pytest.fixture
def configured_batch_project_with_label(
    client,
    dataset,
    data_row,
    wait_for_label_processing,
    rand_gen,
    teardown_helpers,
):
    """Project with a batch having one datarow
    Project contains an ontology with 1 bbox tool
    Additionally includes a create_label method for any needed extra labels
    One label is already created and yielded when using fixture
    """
    project = client.create_project(
        name=rand_gen(str),
        queue_mode=QueueMode.Batch,
        media_type=MediaType.Image,
    )
    data_rows = [dr.uid for dr in list(dataset.data_rows())]
    project._wait_until_data_rows_are_processed(
        data_row_ids=data_rows, sleep_interval=3
    )
    project.create_batch("test-batch", data_rows)
    project.data_row_ids = data_rows

    ontology = _setup_ontology(project)
    label = _create_label(
        project, data_row, ontology, wait_for_label_processing
    )

    yield [project, dataset, data_row, label]

    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)


@pytest.fixture
def configured_batch_project_with_multiple_datarows(
    client,
    dataset,
    data_rows,
    wait_for_label_processing,
    rand_gen,
    teardown_helpers,
):
    """Project with a batch having multiple datarows
    Project contains an ontology with 1 bbox tool
    Additionally includes a create_label method for any needed extra labels
    """
    project = client.create_project(
        name=rand_gen(str),
        queue_mode=QueueMode.Batch,
        media_type=MediaType.Image,
    )
    global_keys = [dr.global_key for dr in data_rows]

    batch_name = f"batch {uuid.uuid4()}"
    project.create_batch(batch_name, global_keys=global_keys)

    ontology = _setup_ontology(project)
    for datarow in data_rows:
        _create_label(project, datarow, ontology, wait_for_label_processing)

    yield [project, dataset, data_rows]

    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)


# NOTE this is nice heuristics, also there is this logic _wait_until_data_rows_are_processed in Project
#    in case we still have flakiness in the future, we can use it
@pytest.fixture
def wait_for_data_row_processing():
    """
    Do not use. Only for testing.

    Returns DataRow after waiting for it to finish processing media_attributes.
    Some tests, specifically ones that rely on label export, rely on
    DataRow be fully processed with media_attributes
    """

    def func(client, data_row, custom_check=None):
        """
        added check_updated_at because when a data_row is updated from say
        an image to pdf, it already has media_attributes and the loop does
        not wait for processing to a pdf
        """
        data_row_id = data_row.uid
        timeout_seconds = 60
        while True:
            data_row = client.get_data_row(data_row_id)
            passed_custom_check = not custom_check or custom_check(data_row)
            if data_row.media_attributes and passed_custom_check:
                return data_row
            timeout_seconds -= 2
            if timeout_seconds <= 0:
                raise TimeoutError(
                    f"Timed out waiting for DataRow '{data_row_id}' to finish processing media_attributes"
                )
            time.sleep(2)

    return func


@pytest.fixture
def wait_for_label_processing():
    """
    Do not use. Only for testing.

    Returns project's labels as a list after waiting for them to finish processing.
    If `project.labels()` is called before label is fully processed,
    it may return an empty set
    """

    def func(project):
        timeout_seconds = 10
        while True:
            labels = list(project.labels())
            if len(labels) > 0:
                return labels
            timeout_seconds -= 2
            if timeout_seconds <= 0:
                raise TimeoutError(
                    f"Timed out waiting for label for project '{project.uid}' to finish processing"
                )
            time.sleep(2)

    return func


@pytest.fixture
def initial_dataset(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    yield dataset

    dataset.delete()


@pytest.fixture
def video_data(client, rand_gen, video_data_row, wait_for_data_row_processing):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_ids = []
    data_row = dataset.create_data_row(video_data_row)
    data_row = wait_for_data_row_processing(client, data_row)
    data_row_ids.append(data_row.uid)
    yield dataset, data_row_ids
    dataset.delete()


def create_video_data_row(rand_gen):
    return {
        "row_data": "https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4",
        "global_key": f"https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4-{rand_gen(str)}",
        "media_type": "VIDEO",
    }


@pytest.fixture
def video_data_100_rows(client, rand_gen, wait_for_data_row_processing):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_ids = []
    for _ in range(100):
        data_row = dataset.create_data_row(create_video_data_row(rand_gen))
        data_row = wait_for_data_row_processing(client, data_row)
        data_row_ids.append(data_row.uid)
    yield dataset, data_row_ids
    dataset.delete()


@pytest.fixture()
def video_data_row(rand_gen):
    return create_video_data_row(rand_gen)


class ExportV2Helpers:
    @classmethod
    def run_project_export_v2_task(
        cls, project, num_retries=5, task_name=None, filters={}, params={}
    ):
        task = None
        params = (
            params
            if params
            else {
                "project_details": True,
                "performance_details": False,
                "data_row_details": True,
                "label_details": True,
            }
        )
        while num_retries > 0:
            task = project.export_v2(
                task_name=task_name, filters=filters, params=params
            )
            task.wait_till_done()
            assert task.status == "COMPLETE"
            assert task.errors is None
            if len(task.result) == 0:
                num_retries -= 1
                time.sleep(5)
            else:
                break
        return task.result

    @classmethod
    def run_dataset_export_v2_task(
        cls, dataset, num_retries=5, task_name=None, filters={}, params={}
    ):
        task = None
        params = (
            params
            if params
            else {"performance_details": False, "label_details": True}
        )
        while num_retries > 0:
            task = dataset.export_v2(
                task_name=task_name, filters=filters, params=params
            )
            task.wait_till_done()
            assert task.status == "COMPLETE"
            assert task.errors is None
            if len(task.result) == 0:
                num_retries -= 1
                time.sleep(5)
            else:
                break

        return task.result

    @classmethod
    def run_catalog_export_v2_task(
        cls, client, num_retries=5, task_name=None, filters={}, params={}
    ):
        task = None
        params = (
            params
            if params
            else {"performance_details": False, "label_details": True}
        )
        catalog = client.get_catalog()
        while num_retries > 0:
            task = catalog.export_v2(
                task_name=task_name, filters=filters, params=params
            )
            task.wait_till_done()
            assert task.status == "COMPLETE"
            assert task.errors is None
            if len(task.result) == 0:
                num_retries -= 1
                time.sleep(5)
            else:
                break

        return task.result


@pytest.fixture
def export_v2_test_helpers() -> Type[ExportV2Helpers]:
    return ExportV2Helpers()


@pytest.fixture
def big_dataset_data_row_ids(big_dataset: Dataset):
    export_task = big_dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    yield [dr.json["data_row"]["id"] for dr in stream]


@pytest.fixture(scope="function")
def dataset_with_invalid_data_rows(
    unique_dataset: Dataset, upload_invalid_data_rows_for_dataset
):
    upload_invalid_data_rows_for_dataset(unique_dataset)

    yield unique_dataset


@pytest.fixture
def upload_invalid_data_rows_for_dataset():
    def _upload_invalid_data_rows_for_dataset(dataset: Dataset):
        task = dataset.create_data_rows(
            [
                {
                    "row_data": "gs://invalid-bucket/example.png",  # forbidden
                    "external_id": "image-without-access.jpg",
                },
            ]
            * 2
        )
        task.wait_till_done()

    return _upload_invalid_data_rows_for_dataset


@pytest.fixture
def configured_project(
    project_with_empty_ontology, initial_dataset, rand_gen, image_url
):
    dataset = initial_dataset
    data_row_id = dataset.create_data_row(row_data=image_url).uid
    project = project_with_empty_ontology

    batch = project.create_batch(
        rand_gen(str),
        [data_row_id],  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = [data_row_id]

    yield project

    batch.delete()


@pytest.fixture
def project_with_empty_ontology(project):
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"
        )
    )[0]
    empty_ontology = {"tools": [], "classifications": []}
    project.setup(editor, empty_ontology)
    yield project


@pytest.fixture
def configured_project_with_complex_ontology(
    client, initial_dataset, rand_gen, image_url, teardown_helpers
):
    project = client.create_project(
        name=rand_gen(str),
        queue_mode=QueueMode.Batch,
        media_type=MediaType.Image,
    )
    dataset = initial_dataset
    data_row = dataset.create_data_row(row_data=image_url)
    data_row_ids = [data_row.uid]

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids

    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"
        )
    )[0]

    ontology = OntologyBuilder()
    tools = [
        Tool(tool=Tool.Type.BBOX, name="test-bbox-class"),
        Tool(tool=Tool.Type.LINE, name="test-line-class"),
        Tool(tool=Tool.Type.POINT, name="test-point-class"),
        Tool(tool=Tool.Type.POLYGON, name="test-polygon-class"),
        Tool(tool=Tool.Type.NER, name="test-ner-class"),
    ]

    options = [
        Option(value="first option answer"),
        Option(value="second option answer"),
        Option(value="third option answer"),
    ]

    classifications = [
        Classification(
            class_type=Classification.Type.TEXT, name="test-text-class"
        ),
        Classification(
            class_type=Classification.Type.RADIO,
            name="test-radio-class",
            options=options,
        ),
        Classification(
            class_type=Classification.Type.CHECKLIST,
            name="test-checklist-class",
            options=options,
        ),
    ]

    for t in tools:
        for c in classifications:
            t.add_classification(c)
        ontology.add_tool(t)
    for c in classifications:
        ontology.add_classification(c)

    project.setup(editor, ontology.asdict())

    yield [project, data_row]
    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)


@pytest.fixture
def embedding(client: Client, environ):
    uuid_str = uuid.uuid4().hex
    time.sleep(randint(1, 5))
    embedding = client.create_embedding(f"sdk-int-{uuid_str}", 8)
    yield embedding

    embedding.delete()


@pytest.fixture
def valid_model_id():
    return "2c903542-d1da-48fd-9db1-8c62571bd3d2"


@pytest.fixture
def requested_labeling_service(
    rand_gen, client, chat_evaluation_ontology, model_config, teardown_helpers
):
    project_name = f"test-model-evaluation-project-{rand_gen(str)}"
    dataset_name = f"test-model-evaluation-dataset-{rand_gen(str)}"
    project = client.create_model_evaluation_project(
        name=project_name, dataset_name=dataset_name, data_row_count=1
    )
    project.connect_ontology(chat_evaluation_ontology)

    project.upsert_instructions("tests/integration/media/sample_pdf.pdf")

    labeling_service = project.get_labeling_service()
    project.add_model_config(model_config.uid)
    project.set_project_model_setup_complete()

    labeling_service.request()

    yield project, project.get_labeling_service()

    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)


class TearDownHelpers:
    @staticmethod
    def teardown_project_labels_ontology_feature_schemas(project: Project):
        """
        Call this function to release project, labels, ontology and feature schemas in fixture teardown

        NOTE: exception handling is not required as this is a fixture teardown
        """
        ontology = project.ontology()
        ontology_id = ontology.uid
        client = project.client
        classification_feature_schema_ids = [
            feature["featureSchemaId"]
            for feature in ontology.normalized["classifications"]
        ]
        tool_feature_schema_ids = [
            feature["featureSchemaId"]
            for feature in ontology.normalized["tools"]
        ]

        feature_schema_ids = (
            classification_feature_schema_ids + tool_feature_schema_ids
        )
        labels = list(project.labels())
        for label in labels:
            label.delete()

        project.delete()
        client.delete_unused_ontology(ontology_id)
        for feature_schema_id in feature_schema_ids:
            try:
                project.client.delete_unused_feature_schema(feature_schema_id)
            except LabelboxError as e:
                print(
                    f"Failed to delete feature schema {feature_schema_id}: {e}"
                )

    @staticmethod
    def teardown_ontology_feature_schemas(ontology: Ontology):
        """
        Call this function to release project, labels, ontology and feature schemas in fixture teardown

        NOTE: exception handling is not required as this is a fixture teardown
        """
        ontology_id = ontology.uid
        client = ontology.client
        classification_feature_schema_ids = [
            feature["featureSchemaId"]
            for feature in ontology.normalized["classifications"]
        ] + [
            option["featureSchemaId"]
            for feature in ontology.normalized["classifications"]
            for option in feature.get("options", [])
        ]

        tool_feature_schema_ids = (
            [
                feature["featureSchemaId"]
                for feature in ontology.normalized["tools"]
            ]
            + [
                classification["featureSchemaId"]
                for tool in ontology.normalized["tools"]
                for classification in tool.get("classifications", [])
            ]
            + [
                option["featureSchemaId"]
                for tool in ontology.normalized["tools"]
                for classification in tool.get("classifications", [])
                for option in classification.get("options", [])
            ]
        )

        feature_schema_ids = (
            classification_feature_schema_ids + tool_feature_schema_ids
        )

        client.delete_unused_ontology(ontology_id)
        for feature_schema_id in feature_schema_ids:
            try:
                project.client.delete_unused_feature_schema(feature_schema_id)
            except LabelboxError as e:
                print(
                    f"Failed to delete feature schema {feature_schema_id}: {e}"
                )


class ModuleTearDownHelpers(TearDownHelpers): ...


@pytest.fixture
def teardown_helpers():
    return TearDownHelpers()


@pytest.fixture(scope="module")
def module_teardown_helpers():
    return TearDownHelpers()
