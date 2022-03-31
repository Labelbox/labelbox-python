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
from labelbox import OntologyBuilder, Tool, Option, Classification
from labelbox.orm import query
from labelbox.pagination import PaginatedCollection
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.invite import Invite
from labelbox.schema.user import User

IMG_URL = "https://picsum.photos/200/300"


class Environ(Enum):
    LOCAL = 'local'
    PROD = 'prod'
    STAGING = 'staging'


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
        return 'https://staging-api.labelbox.com/graphql'
    return 'http://host.docker.internal:8080/graphql'


def testing_api_key(environ: str) -> str:
    if environ == Environ.PROD:
        return os.environ["LABELBOX_TEST_API_KEY_PROD"]
    elif environ == Environ.STAGING:
        return os.environ["LABELBOX_TEST_API_KEY_STAGING"]
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
        super().__init__(api_key, api_url, enable_experimental=True)
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
    return client.upload_data(requests.get(IMG_URL).content, sign=True)


@pytest.fixture
def project(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    yield project
    project.delete()


@pytest.fixture
def dataset(client, rand_gen):
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
    dr = next(dataset.data_rows())
    yield dr
    dr.delete()


@pytest.fixture
def iframe_url(environ) -> str:
    if environ in [Environ.PROD, Environ.LOCAL]:
        return 'https://editor.labelbox.com'
    elif environ == Environ.STAGING:
        return 'https://staging.labelbox.dev/editor'


@pytest.fixture
def sample_video() -> str:
    path_to_video = 'tests/integration/media/cat.mp4'
    assert os.path.exists(path_to_video)
    return path_to_video


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
                                  datarow):
    """Project with a connected dataset, having one datarow
    Project contains an ontology with 1 bbox tool
    Additionally includes a create_label method for any needed extra labels
    One label is already created and yielded when using fixture
    """
    project.datasets.connect(dataset)
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]

    ontology_builder = OntologyBuilder(tools=[
        Tool(tool=Tool.Type.BBOX, name="test-bbox-class"),
    ])
    project.setup(editor, ontology_builder.asdict())
    # TODO: ontology may not be synchronous after setup. remove sleep when api is more consistent
    time.sleep(2)

    ontology = ontology_builder.from_project(project)
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
            client, project.uid, f'label-import-{uuid.uuid4()}', predictions)
        upload_task.wait_until_done(sleep_time_seconds=5)

    project.create_label = create_label
    project.create_label()
    label = next(project.labels())
    yield [project, dataset, datarow, label]

    for label in project.labels():
        label.delete()


@pytest.fixture
def configured_project_with_complex_ontology(client, rand_gen, image_url):
    project = client.create_project(name=rand_gen(str))
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
                       instructions="test-text-class"),
        Classification(class_type=Classification.Type.DROPDOWN,
                       instructions="test-dropdown-class",
                       options=options),
        Classification(class_type=Classification.Type.RADIO,
                       instructions="test-radio-class",
                       options=options),
        Classification(class_type=Classification.Type.CHECKLIST,
                       instructions="test-checklist-class",
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
