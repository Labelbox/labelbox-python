import os
import re
import uuid
import time
from collections import namedtuple
from datetime import datetime
from enum import Enum
from random import randint
from string import ascii_letters
from types import SimpleNamespace

import pytest
import requests

from labelbox import Client
from labelbox import LabelingFrontend
from labelbox.orm import query
from labelbox.schema.annotation_import import MALPredictionImport
from labelbox.orm.db_object import Entity, DbObject
from labelbox.pagination import PaginatedCollection
from labelbox.schema.invite import Invite
from labelbox.schema.user import User
from labelbox import OntologyBuilder, Tool

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
                               cursor_path=['project', 'invites', 'nextCursor'],
                               experimental=True)


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
def rand_gen():

    def gen(field_type):
        if field_type is str:
            return "".join(ascii_letters[randint(0,
                                                 len(ascii_letters) - 1)]
                           for _ in range(16))

        if field_type is datetime:
            return datetime.now()

        raise Exception("Can't random generate for field type '%r'" %
                        field_type)

    return gen


@pytest.fixture
def project(client, rand_gen):
    project = client.create_project(name=rand_gen(str))

    def create_label(**kwargs):
        """ Creates a label on a Legacy Editor project. Not supported in the new Editor.
        Args:
            **kwargs: Label attributes. At minimum, the label `DataRow`.
        """
        Label = Entity.Label
        kwargs[Label.project] = project
        kwargs[Label.seconds_to_label] = kwargs.get(Label.seconds_to_label.name,
                                                    0.0)
        data = {
            Label.attribute(attr) if isinstance(attr, str) else attr:
            value.uid if isinstance(value, DbObject) else value
            for attr, value in kwargs.items()
        }
        query_str, params = query.create(Label, data)
        query_str = query_str.replace(
            "data: {", "data: {type: {connect: {name: \"Any\"}} ")
        res = project.client.execute(query_str, params)
        return Label(project.client, res["createLabel"])

    project.create_label = create_label
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


LabelPack = namedtuple("LabelPack", "project dataset data_row label")


@pytest.fixture
def label_pack(project, rand_gen, image_url):
    client = project.client
    dataset = client.create_dataset(name=rand_gen(str))
    project.datasets.connect(dataset)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    label = project.create_label(data_row=data_row, label=rand_gen(str))
    time.sleep(10)
    yield LabelPack(project, dataset, data_row, label)
    dataset.delete()


@pytest.fixture
def iframe_url(environ) -> str:
    if environ == Environ.PROD:
        return 'https://editor.labelbox.com'
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
def annotation_submit_fn(client):

    def submit(project_id, data_row_id):
        feature_result = client.execute(
            """query featuresPyApi ($project_id : ID!, $datarow_id: ID!
            ) {project(where: { id: $project_id }) {
                    featuresForDataRow(where: {dataRow: { id: $datarow_id }}) {id}}}
            """, {
                "project_id": project_id,
                "datarow_id": data_row_id
            })
        features = feature_result['project']['featuresForDataRow']
        feature_ids = [feature['id'] for feature in features]
        client.execute(
            """mutation createLabelPyApi ($project_id : ID!,$datarow_id: ID!,$feature_ids: [ID!]!,$time_seconds : Float!) {
                createLabelFromFeatures(data: {dataRow: { id: $datarow_id },project: { id: $project_id },
                    featureIds: $feature_ids,secondsSpent: $time_seconds}) {id}}""",
            {
                "project_id": project_id,
                "datarow_id": data_row_id,
                "feature_ids": feature_ids,
                "time_seconds": 10
            })

    return submit


@pytest.fixture
def configured_project_with_label(client, rand_gen, annotation_submit_fn,
                                  image_url):
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=image_url)
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]

    ontology_builder = OntologyBuilder(tools=[
        Tool(tool=Tool.Type.BBOX, name="test-bbox-class"),
    ])
    project.setup(editor, ontology_builder.asdict())
    project.enable_model_assisted_labeling()
    ontology = ontology_builder.from_project(project)
    predictions = [{
        "uuid": str(uuid.uuid4()),
        "schemaId": ontology.tools[0].feature_schema_id,
        "dataRow": {
            "id": data_row.uid
        },
        "bbox": {
            "top": 20,
            "left": 20,
            "height": 50,
            "width": 50
        }
    }]
    upload_task = MALPredictionImport.create_from_objects(
        client, project.uid, f'mal-import-{uuid.uuid4()}', predictions)
    upload_task.wait_until_done()
    time.sleep(2)
    annotation_submit_fn(project.uid, data_row.uid)
    time.sleep(2)
    yield project
    dataset.delete()
    project.delete()
