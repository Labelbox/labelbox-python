import json
import os
import re
import time
import uuid
from enum import Enum
from types import SimpleNamespace

import pytest
import requests

from labelbox import Client
from labelbox import LabelingFrontend
from labelbox import OntologyBuilder, Tool, Option, Classification, MediaType
from labelbox.orm import query
from labelbox.pagination import PaginatedCollection
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.enums import AnnotationImportState
from labelbox.schema.invite import Invite
from labelbox.schema.queue_mode import QueueMode
from labelbox.schema.user import User

IMG_URL = "https://picsum.photos/200/300.jpg"


class Environ(Enum):
    LOCAL = 'local'
    PROD = 'prod'
    STAGING = 'staging'
    ONPREM = 'onprem'
    CUSTOM = 'custom'


@pytest.fixture(scope="session")
def environ() -> Environ:
    """
    Checks environment variables for LABELBOX_ENVIRON to be
    'prod' or 'staging'

    Make sure to set LABELBOX_TEST_ENVIRON in .github/workflows/python-package.yaml

    """
    try:
        return Environ(os.environ['LABELBOX_TEST_ENVIRON'])
    except KeyError:
        raise Exception(f'Missing LABELBOX_TEST_ENVIRON in: {os.environ}')


def graphql_url(environ: str) -> str:
    if environ == Environ.PROD:
        return 'https://api.labelbox.com/graphql'
    elif environ == Environ.STAGING:
        return 'https://api.lb-stage.xyz/graphql'
    elif environ == Environ.ONPREM:
        hostname = os.environ.get('LABELBOX_TEST_ONPREM_HOSTNAME', None)
        if hostname is None:
            raise Exception(f"Missing LABELBOX_TEST_ONPREM_INSTANCE")
        return f"{hostname}/api/_gql"
    elif environ == Environ.CUSTOM:
        graphql_api_endpoint = os.environ.get(
            'LABELBOX_TEST_GRAPHQL_API_ENDPOINT')
        if graphql_api_endpoint is None:
            raise Exception(f"Missing LABELBOX_TEST_GRAPHQL_API_ENDPOINT")
        return graphql_api_endpoint
    return 'http://host.docker.internal:8080/graphql'


def rest_url(environ: str) -> str:
    if environ == Environ.PROD:
        return 'https://api.labelbox.com/api/v1'
    elif environ == Environ.STAGING:
        return 'https://api.lb-stage.xyz/api/v1'
    elif environ == Environ.CUSTOM:
        rest_api_endpoint = os.environ.get('LABELBOX_TEST_REST_API_ENDPOINT')
        if rest_api_endpoint is None:
            raise Exception(f"Missing LABELBOX_TEST_REST_API_ENDPOINT")
        return rest_api_endpoint
    return 'http://host.docker.internal:8080/api/v1'


def testing_api_key(environ: str) -> str:
    if environ == Environ.PROD:
        return os.environ["LABELBOX_TEST_API_KEY_PROD"]
    elif environ == Environ.STAGING:
        return os.environ["LABELBOX_TEST_API_KEY_STAGING"]
    elif environ == Environ.ONPREM:
        return os.environ["LABELBOX_TEST_API_KEY_ONPREM"]
    elif environ == Environ.CUSTOM:
        return os.environ["LABELBOX_TEST_API_KEY_CUSTOM"]
    return os.environ["LABELBOX_TEST_API_KEY_LOCAL"]


def cancel_invite(client, invite_id):
    """
    Do not use. Only for testing.
    """
    query_str = """mutation CancelInvitePyApi($where: WhereUniqueIdInput!) {
            cancelInvite(where: $where) {id}}"""
    client.execute(query_str, {'where': {'id': invite_id}}, experimental=True)


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
    return PaginatedCollection(client,
                               query_str, {id_param: project_id},
                               ['project', 'invites', 'nodes'],
                               Invite,
                               cursor_path=['project', 'invites', 'nextCursor'])


def get_invites(client):
    """
    Do not use. Only for testing.
    """
    query_str = """query GetOrgInvitationsPyApi($from: ID, $first: PageSize) {
            organization { id invites(from: $from, first: $first) {
                nodes { id createdAt organizationRoleName inviteeEmail } nextCursor }}}"""
    invites = PaginatedCollection(
        client,
        query_str, {}, ['organization', 'invites', 'nodes'],
        Invite,
        cursor_path=['organization', 'invites', 'nextCursor'],
        experimental=True)
    return invites


@pytest.fixture
def queries():
    return SimpleNamespace(cancel_invite=cancel_invite,
                           get_project_invites=get_project_invites,
                           get_invites=get_invites)


class IntegrationClient(Client):

    def __init__(self, environ: str) -> None:
        api_url = graphql_url(environ)
        api_key = testing_api_key(environ)
        rest_endpoint = rest_url(environ)
        super().__init__(api_key,
                         api_url,
                         enable_experimental=True,
                         rest_endpoint=rest_endpoint)
        self.queries = []

    def execute(self, query=None, params=None, check_naming=True, **kwargs):
        if check_naming and query is not None:
            assert re.match(r"(?:query|mutation) \w+PyApi", query) is not None
        self.queries.append((query, params))
        return super().execute(query, params, **kwargs)


@pytest.fixture(scope="session")
def client(environ: str):
    return IntegrationClient(environ)


@pytest.fixture(scope="session")
def image_url(client):
    return client.upload_data(requests.get(IMG_URL).content,
                              content_type="image/jpeg",
                              filename="image.jpeg",
                              sign=True)


@pytest.fixture(scope="session")
def pdf_url(client):
    return client.upload_file('tests/assets/loremipsum.pdf')


@pytest.fixture
def project(client, rand_gen):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Dataset)
    yield project
    project.delete()


@pytest.fixture
def batch_project(client, rand_gen):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Batch)
    yield project
    project.delete()


@pytest.fixture
def consensus_project(client, rand_gen):
    project = client.create_project(name=rand_gen(str),
                                    auto_audit_percentage=0,
                                    queue_mode=QueueMode.Dataset)
    yield project
    project.delete()


@pytest.fixture
def dataset(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    yield dataset
    dataset.delete()


@pytest.fixture(scope='function')
def unique_dataset(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    yield dataset
    dataset.delete()


@pytest.fixture
def datarow(dataset, image_url):
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ])
    task.wait_till_done()
    dr = dataset.data_rows().get_one()
    yield dr
    dr.delete()


@pytest.fixture()
def data_rows(dataset, image_url):
    dr1 = dict(row_data=image_url, global_key=f"global-key-{uuid.uuid4()}")
    dr2 = dict(row_data=image_url, global_key=f"global-key-{uuid.uuid4()}")
    task = dataset.create_data_rows([dr1, dr2])
    task.wait_till_done()

    drs = list(dataset.export_data_rows())
    yield drs

    for dr in drs:
        dr.delete()


@pytest.fixture
def iframe_url(environ) -> str:
    if environ in [Environ.PROD, Environ.LOCAL]:
        return 'https://editor.labelbox.com'
    elif environ == Environ.STAGING:
        return 'https://editor.lb-stage.xyz'


@pytest.fixture
def sample_image() -> str:
    path_to_video = 'tests/integration/media/sample_image.jpg'
    return path_to_video


@pytest.fixture
def sample_video() -> str:
    path_to_video = 'tests/integration/media/cat.mp4'
    return path_to_video


@pytest.fixture
def sample_bulk_conversation() -> list:
    path_to_conversation = 'tests/integration/media/bulk_conversation.json'
    with open(path_to_conversation) as json_file:
        conversations = json.load(json_file)
    return conversations


@pytest.fixture
def organization(client):
    # Must have at least one seat open in your org to run these tests
    org = client.get_organization()
    # Clean up before and after incase this wasn't run for some reason.
    for invite in get_invites(client):
        if "@labelbox.com" in invite.email:
            cancel_invite(client, invite.uid)
    yield org
    for invite in get_invites(client):
        if "@labelbox.com" in invite.email:
            cancel_invite(client, invite.uid)


@pytest.fixture
def project_based_user(client, rand_gen):
    email = rand_gen(str)
    # Use old mutation because it doesn't require users to accept email invites
    query_str = """mutation MakeNewUserPyApi {
        addMembersToOrganization(
            data: {
                emails: ["%s@labelbox.com"],
                orgRoleId: "%s",
                projectRoles: []
            }
        ) {
        newUserId
        }
    }
    """ % (email, str(client.get_roles()['NONE'].uid))
    user_id = client.execute(
        query_str)['addMembersToOrganization'][0]['newUserId']
    assert user_id is not None, "Unable to add user with old mutation"
    user = client._get_single(User, user_id)
    yield user
    client.get_organization().remove_user(user)


@pytest.fixture
def project_pack(client):
    projects = [
        client.create_project(name=f"user-proj-{idx}") for idx in range(2)
    ]
    yield projects
    for proj in projects:
        proj.delete()


@pytest.fixture
def configured_project(project, client, rand_gen, image_url):
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    dataset.create_data_row(row_data=image_url)
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    empty_ontology = {"tools": [], "classifications": []}
    project.setup(editor, empty_ontology)
    yield project
    dataset.delete()
    project.delete()


@pytest.fixture
def configured_project_with_label(client, rand_gen, image_url, project, dataset,
                                  datarow, wait_for_label_processing):
    """Project with a connected dataset, having one datarow
    Project contains an ontology with 1 bbox tool
    Additionally includes a create_label method for any needed extra labels
    One label is already created and yielded when using fixture
    """
    project.datasets.connect(dataset)

    ontology = _setup_ontology(project)
    label = _create_label(project, datarow, ontology, wait_for_label_processing)

    yield [project, dataset, datarow, label]

    for label in project.labels():
        label.delete()


@pytest.fixture
def configured_batch_project_with_label(client, rand_gen, image_url,
                                        batch_project, dataset, datarow,
                                        wait_for_label_processing):
    """Project with a batch having one datarow
    Project contains an ontology with 1 bbox tool
    Additionally includes a create_label method for any needed extra labels
    One label is already created and yielded when using fixture
    """
    data_rows = [dr.uid for dr in list(dataset.data_rows())]
    batch_project.create_batch("test-batch", data_rows)

    ontology = _setup_ontology(batch_project)
    label = _create_label(batch_project, datarow, ontology,
                          wait_for_label_processing)

    yield [batch_project, dataset, datarow, label]

    for label in batch_project.labels():
        label.delete()


def _create_label(project, datarow, ontology, wait_for_label_processing):
    predictions = [{
        "uuid": str(uuid.uuid4()),
        "schemaId": ontology.tools[0].feature_schema_id,
        "dataRow": {
            "id": datarow.uid
        },
        "bbox": {
            "top": 20,
            "left": 20,
            "height": 50,
            "width": 50
        }
    }]

    def create_label():
        """ Ad-hoc function to create a LabelImport
        Creates a LabelImport task which will create a label
        """
        upload_task = LabelImport.create_from_objects(
            project.client, project.uid, f'label-import-{uuid.uuid4()}',
            predictions)
        upload_task.wait_until_done(sleep_time_seconds=5)
        assert upload_task.state == AnnotationImportState.FINISHED, "Label Import did not finish"
        assert len(
            upload_task.errors
        ) == 0, f"Label Import {upload_task.name} failed with errors {upload_task.errors}"

    project.create_label = create_label
    project.create_label()
    label = wait_for_label_processing(project)[0]
    return label


def _setup_ontology(project):
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    ontology_builder = OntologyBuilder(tools=[
        Tool(tool=Tool.Type.BBOX, name="test-bbox-class"),
    ])
    project.setup(editor, ontology_builder.asdict())
    # TODO: ontology may not be synchronous after setup. remove sleep when api is more consistent
    time.sleep(2)
    return ontology_builder.from_project(project)


@pytest.fixture
def configured_project_with_complex_ontology(client, rand_gen, image_url):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Dataset)
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=image_url)
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]

    ontology = OntologyBuilder()
    tools = [
        Tool(tool=Tool.Type.BBOX, name="test-bbox-class"),
        Tool(tool=Tool.Type.LINE, name="test-line-class"),
        Tool(tool=Tool.Type.POINT, name="test-point-class"),
        Tool(tool=Tool.Type.POLYGON, name="test-polygon-class"),
        Tool(tool=Tool.Type.NER, name="test-ner-class")
    ]

    options = [
        Option(value="first option answer"),
        Option(value="second option answer"),
        Option(value="third option answer")
    ]

    classifications = [
        Classification(class_type=Classification.Type.TEXT,
                       name="test-text-class"),
        Classification(class_type=Classification.Type.DROPDOWN,
                       name="test-dropdown-class",
                       options=options),
        Classification(class_type=Classification.Type.RADIO,
                       name="test-radio-class",
                       options=options),
        Classification(class_type=Classification.Type.CHECKLIST,
                       name="test-checklist-class",
                       options=options)
    ]

    for t in tools:
        for c in classifications:
            t.add_classification(c)
        ontology.add_tool(t)
    for c in classifications:
        ontology.add_classification(c)

    project.setup(editor, ontology.asdict())

    yield [project, data_row]
    dataset.delete()
    project.delete()


@pytest.fixture
def wait_for_data_row_processing():
    """
    Do not use. Only for testing.

    Returns DataRow after waiting for it to finish processing media_attributes.
    Some tests, specifically ones that rely on label export, rely on
    DataRow be fully processed with media_attributes
    """

    def func(client, data_row):
        data_row_id = data_row.uid
        timeout_seconds = 60
        while True:
            data_row = client.get_data_row(data_row_id)
            if data_row.media_attributes:
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
def ontology(client):
    ontology_builder = OntologyBuilder(
        tools=[
            Tool(tool=Tool.Type.BBOX, name="Box 1", color="#ff0000"),
            Tool(tool=Tool.Type.BBOX, name="Box 2", color="#ff0000")
        ],
        classifications=[
            Classification(name="Root Class",
                           class_type=Classification.Type.RADIO,
                           options=[
                               Option(value="1", label="Option 1"),
                               Option(value="2", label="Option 2")
                           ])
        ])
    ontology = client.create_ontology('Integration Test Ontology',
                                      ontology_builder.asdict(),
                                      MediaType.Image)
    yield ontology
    client.delete_unused_ontology(ontology.uid)
