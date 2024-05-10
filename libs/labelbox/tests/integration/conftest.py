from collections import defaultdict
from itertools import islice
import json
import os
import sys
import re
import time
import uuid
import requests
from types import SimpleNamespace
from typing import Type, List
from enum import Enum
from typing import Tuple

import pytest
import requests

from labelbox import Dataset, DataRow
from labelbox import LabelingFrontend
from labelbox import OntologyBuilder, Tool, Option, Classification, MediaType
from labelbox.orm import query
from labelbox.pagination import PaginatedCollection
from labelbox.schema.annotation_import import LabelImport
from labelbox.schema.catalog import Catalog
from labelbox.schema.enums import AnnotationImportState
from labelbox.schema.invite import Invite
from labelbox.schema.quality_mode import QualityMode
from labelbox.schema.queue_mode import QueueMode
from labelbox.schema.user import User
from labelbox import Client
from labelbox.schema.ontology_kind import OntologyKind


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
        client.create_project(name=f"user-proj-{idx}",
                              queue_mode=QueueMode.Batch,
                              media_type=MediaType.Image) for idx in range(2)
    ]
    yield projects
    for proj in projects:
        proj.delete()


@pytest.fixture
def project_with_empty_ontology(project):
    editor = list(
        project.client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    empty_ontology = {"tools": [], "classifications": []}
    project.setup(editor, empty_ontology)
    yield project


@pytest.fixture
def configured_project(project_with_empty_ontology, initial_dataset, rand_gen,
                       image_url):
    dataset = initial_dataset
    data_row_id = dataset.create_data_row(row_data=image_url).uid
    project = project_with_empty_ontology

    batch = project.create_batch(
        rand_gen(str),
        [data_row_id],  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = [data_row_id]

    yield project

    batch.delete()


@pytest.fixture
def configured_project_with_complex_ontology(client, initial_dataset, rand_gen,
                                             image_url):
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Batch,
                                    media_type=MediaType.Image)
    dataset = initial_dataset
    data_row = dataset.create_data_row(row_data=image_url)
    data_row_ids = [data_row.uid]

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids

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
    project.delete()


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
        "row_data":
            "https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4",
        "global_key":
            f"https://storage.googleapis.com/labelbox-datasets/video-sample-data/sample-video-1.mp4-{rand_gen(str)}",
        "media_type":
            "VIDEO",
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
    def run_project_export_v2_task(cls,
                                   project,
                                   num_retries=5,
                                   task_name=None,
                                   filters={},
                                   params={}):
        task = None
        params = params if params else {
            "project_details": True,
            "performance_details": False,
            "data_row_details": True,
            "label_details": True
        }
        while (num_retries > 0):
            task = project.export_v2(task_name=task_name,
                                     filters=filters,
                                     params=params)
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
    def run_dataset_export_v2_task(cls,
                                   dataset,
                                   num_retries=5,
                                   task_name=None,
                                   filters={},
                                   params={}):
        task = None
        params = params if params else {
            "performance_details": False,
            "label_details": True
        }
        while (num_retries > 0):
            task = dataset.export_v2(task_name=task_name,
                                     filters=filters,
                                     params=params)
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
    def run_catalog_export_v2_task(cls,
                                   client,
                                   num_retries=5,
                                   task_name=None,
                                   filters={},
                                   params={}):
        task = None
        params = params if params else {
            "performance_details": False,
            "label_details": True
        }
        catalog = client.get_catalog()
        while (num_retries > 0):

            task = catalog.export_v2(task_name=task_name,
                                     filters=filters,
                                     params=params)
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
    yield [dr.uid for dr in list(big_dataset.export_data_rows())]


@pytest.fixture(scope='function')
def dataset_with_invalid_data_rows(unique_dataset: Dataset,
                                   upload_invalid_data_rows_for_dataset):
    upload_invalid_data_rows_for_dataset(unique_dataset)

    yield unique_dataset


@pytest.fixture
def upload_invalid_data_rows_for_dataset():

    def _upload_invalid_data_rows_for_dataset(dataset: Dataset):
        task = dataset.create_data_rows([
            {
                "row_data": 'gs://invalid-bucket/example.png',  # forbidden
                "external_id": "image-without-access.jpg"
            },
        ] * 2)
        task.wait_till_done()

    return _upload_invalid_data_rows_for_dataset


@pytest.fixture
def chat_evaluation_ontology(client, rand_gen):
    ontology_name = f"test-chat-evaluation-ontology-{rand_gen(str)}"
    ontology_builder = OntologyBuilder(
        tools=[
            Tool(tool=Tool.Type.MESSAGE_SINGLE_SELECTION,
                 name="model output single selection"),
            Tool(tool=Tool.Type.MESSAGE_MULTI_SELECTION,
                 name="model output multi selection"),
            Tool(tool=Tool.Type.MESSAGE_RANKING,
                 name="model output multi ranking"),
        ],
        classifications=[
            Classification(class_type=Classification.Type.TEXT,
                           name="global model output text classification",
                           scope=Classification.Scope.GLOBAL),
            Classification(class_type=Classification.Type.RADIO,
                           name="global model output radio classification",
                           scope=Classification.Scope.GLOBAL,
                           options=[
                               Option(value="global first option answer"),
                               Option(value="global second option answer"),
                           ]),
            Classification(class_type=Classification.Type.CHECKLIST,
                           name="global model output checklist classification",
                           scope=Classification.Scope.GLOBAL,
                           options=[
                               Option(value="global first option answer"),
                               Option(value="global second option answer"),
                           ]),
            Classification(class_type=Classification.Type.TEXT,
                           name="index model output text classification",
                           scope=Classification.Scope.INDEX),
            Classification(class_type=Classification.Type.RADIO,
                           name="index model output radio classification",
                           scope=Classification.Scope.INDEX,
                           options=[
                               Option(value="index first option answer"),
                               Option(value="index second option answer"),
                           ]),
            Classification(class_type=Classification.Type.CHECKLIST,
                           name="index model output checklist classification",
                           scope=Classification.Scope.INDEX,
                           options=[
                               Option(value="index first option answer"),
                               Option(value="index second option answer"),
                           ]),
        ])

    ontology = client.create_ontology(
        ontology_name,
        ontology_builder.asdict(),
        media_type=MediaType.Conversational,
        ontology_kind=OntologyKind.ModelEvaluation)

    yield ontology

    client.delete_unused_ontology(ontology.uid)


@pytest.fixture
def chat_evaluation_project_create_dataset(client, rand_gen):
    project_name = f"test-model-evaluation-project-{rand_gen(str)}"
    dataset_name = f"test-model-evaluation-dataset-{rand_gen(str)}"
    project = client.create_model_evaluation_project(name=project_name,
                                                     dataset_name=dataset_name,
                                                     data_row_count=1)

    yield project

    project.delete()


@pytest.fixture
def chat_evaluation_project_append_to_dataset(client, dataset, rand_gen):
    project_name = f"test-model-evaluation-project-{rand_gen(str)}"
    dataset_id = dataset.uid
    project = client.create_model_evaluation_project(name=project_name,
                                                     dataset_id=dataset_id,
                                                     data_row_count=1)

    yield project

    project.delete()


def pytest_configure():
    pytest.report = defaultdict(int)


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef):
    start = time.time()
    yield
    end = time.time()

    exec_time = end - start
    if "FIXTURE_PROFILE" in os.environ:
        pytest.report[fixturedef.argname] += exec_time


@pytest.fixture(scope='session', autouse=True)
def print_perf_summary():
    yield

    if "FIXTURE_PROFILE" in os.environ:
        sorted_dict = dict(
            sorted(pytest.report.items(),
                   key=lambda item: item[1],
                   reverse=True))
        num_of_entries = 10 if len(sorted_dict) >= 10 else len(sorted_dict)
        slowest_fixtures = [(aaa, sorted_dict[aaa])
                            for aaa in islice(sorted_dict, num_of_entries)]
        print("\nTop slowest fixtures:\n", slowest_fixtures, file=sys.stderr)
