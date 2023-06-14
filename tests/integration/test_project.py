import time
import os
from typing import Tuple
import uuid

import pytest
import requests

from labelbox import Project, LabelingFrontend, Dataset
from labelbox.exceptions import InvalidQueryError
from labelbox.schema.data_row import DataRow
from labelbox.schema.label import Label
from labelbox.schema.media_type import MediaType
from labelbox.schema.queue_mode import QueueMode


def test_project(client, rand_gen):

    data = {
        "name": rand_gen(str),
        "description": rand_gen(str),
        "queue_mode": QueueMode.Dataset
    }
    project = client.create_project(**data)
    assert project.name == data["name"]
    assert project.description == data["description"]

    project = client.get_project(project.uid)
    assert project.name == data["name"]
    assert project.description == data["description"]

    update_data = {"name": rand_gen(str), "description": rand_gen(str)}
    project.update(**update_data)
    # Test local object updates.
    assert project.name == update_data["name"]
    assert project.description == update_data["description"]

    # Test remote updates.
    project = client.get_project(project.uid)
    assert project.name == update_data["name"]
    assert project.description == update_data["description"]

    project.delete()
    projects = list(client.get_projects())
    assert project not in projects


def test_batch_project_export_v2(
        configured_batch_project_with_label: Tuple[Project, Dataset, DataRow,
                                                   Label],
        export_v2_test_helpers, dataset: Dataset, image_url: str):
    project, dataset, *_ = configured_batch_project_with_label

    batch = list(project.batches())[0]
    filters = {
        "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "batch_ids": [batch.uid],
    }
    params = {
        "include_performance_details": True,
        "include_labels": True,
        "media_type_override": MediaType.Image
    }
    task_name = "test_batch_export_v2"
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ] * 2)
    task.wait_till_done()
    data_rows = [dr.uid for dr in list(dataset.export_data_rows())]
    batch_one = f'batch one {uuid.uuid4()}'

    # This test creates two batches, only one batch should be exporter
    # Creatin second batch that will not be used in the export due to the filter: batch_id
    project.create_batch(batch_one, data_rows)

    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters, params=params)
    assert (batch.size == len(task_results))


def test_project_export_v2(client, export_v2_test_helpers,
                           configured_project_with_label,
                           wait_for_data_row_processing):
    project, _, data_row, label = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    label_id = label.uid

    task_name = "test_label_export_v2"

    filters = {
        "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"]
    }

    # TODO: Right now we don't have a way to test this
    include_performance_details = True
    params = {
        "include_performance_details": include_performance_details,
        "include_labels": True,
        "media_type_override": MediaType.Image
    }

    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters, params=params)

    for task_result in task_results:
        task_project = task_result['projects'][project.uid]
        task_project_label_ids_set = set(
            map(lambda prediction: prediction['id'], task_project['labels']))
        assert label_id in task_project_label_ids_set

        # TODO: Add back in when we have a way to test this
        # if include_performance_details:
        #     assert 'include_performance_details' in task_result and task_result[
        #         'include_performance_details'] is not None
        # else:
        #     assert 'include_performance_details' not in task_result or task_result[
        #         'include_performance_details'] is None

    filters = {"last_activity_at": [None, "2050-01-01 00:00:00"]}
    export_v2_test_helpers.run_project_export_v2_task(project, filters=filters)

    filters = {"label_created_at": ["2000-01-01 00:00:00", None]}
    export_v2_test_helpers.run_project_export_v2_task(project, filters=filters)


def test_project_export_v2_with_iso_date_filters(client, export_v2_test_helpers,
                                                 configured_project_with_label,
                                                 wait_for_data_row_processing):
    project, _, data_row, label = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    label_id = label.uid

    task_name = "test_label_export_v2_with_iso_date_filters"

    filters = {
        "last_activity_at": [
            "2000-01-01T00:00:00+0230", "2050-01-01T00:00:00+0230"
        ],
        "label_created_at": [
            "2000-01-01T00:00:00+0230", "2050-01-01T00:00:00+0230"
        ]
    }
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters)
    assert label_id == task_results[0]['projects'][
        project.uid]['labels'][0]['id']

    filters = {"last_activity_at": [None, "2050-01-01T00:00:00+0230"]}
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters)
    assert label_id == task_results[0]['projects'][
        project.uid]['labels'][0]['id']

    filters = {"label_created_at": ["2050-01-01T00:00:00+0230", None]}
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters)
    assert len(task_results) == 0


@pytest.mark.parametrize("data_rows", [3], indirect=True)
def test_project_export_v2_datarow_list(
        export_v2_test_helpers,
        configured_batch_project_with_multiple_datarows):
    batch_project, _, data_rows = configured_batch_project_with_multiple_datarows

    data_row_ids = [dr.uid for dr in data_rows]
    datarow_filter_size = 2

    filters = {
        "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "data_row_ids": data_row_ids[:datarow_filter_size]
    }
    params = {"data_row_details": True, "media_type_override": MediaType.Image}
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        batch_project, filters=filters, params=params)

    # only 2 datarows should be exported
    assert len(task_results) == datarow_filter_size
    # only filtered datarows should be exported
    assert set([dr['data_row']['id'] for dr in task_results
               ]) == set(data_row_ids[:datarow_filter_size])


def test_update_project_resource_tags(client, rand_gen):

    def delete_tag(tag_id: str):
        """Deletes a tag given the tag uid. Currently internal use only so this is not public"""
        res = client.execute(
            """mutation deleteResourceTagPyApi($tag_id: String!) {
        deleteResourceTag(input: {id: $tag_id}) {
            id
        }
        }
        """, {"tag_id": tag_id})
        return res

    before = list(client.get_projects())
    for o in before:
        assert isinstance(o, Project)

    org = client.get_organization()
    assert org.uid is not None

    project_name = rand_gen(str)
    p1 = client.create_project(name=project_name)
    assert p1.uid is not None

    colorA = "#ffffff"
    textA = rand_gen(str)
    tag = {"text": textA, "color": colorA}

    colorB = colorA
    textB = rand_gen(str)
    tagB = {"text": textB, "color": colorB}

    tagA = client.get_organization().create_resource_tag(tag)
    assert tagA.text == textA
    assert '#' + tagA.color == colorA
    assert tagA.uid is not None

    tags = org.get_resource_tags()
    lenA = len(tags)
    assert lenA > 0

    tagB = client.get_organization().create_resource_tag(tagB)
    assert tagB.text == textB
    assert '#' + tagB.color == colorB
    assert tagB.uid is not None

    tags = client.get_organization().get_resource_tags()
    lenB = len(tags)
    assert lenB > 0
    assert lenB > lenA

    project_resource_tag = client.get_project(
        p1.uid).update_project_resource_tags([str(tagA.uid)])
    assert len(project_resource_tag) == 1
    assert project_resource_tag[0].uid == tagA.uid

    delete_tag(tagA.uid)
    delete_tag(tagB.uid)


def test_project_filtering(client, rand_gen):
    name_1 = rand_gen(str)
    name_2 = rand_gen(str)
    p1 = client.create_project(name=name_1)
    p2 = client.create_project(name=name_2)

    assert list(client.get_projects(where=Project.name == name_1)) == [p1]
    assert list(client.get_projects(where=Project.name == name_2)) == [p2]

    p1.delete()
    p2.delete()


def test_upsert_review_queue(project):
    project.upsert_review_queue(0.6)

    with pytest.raises(ValueError) as exc_info:
        project.upsert_review_queue(1.001)
    assert str(exc_info.value) == "Quota factor must be in the range of [0,1]"

    with pytest.raises(ValueError) as exc_info:
        project.upsert_review_queue(-0.001)
    assert str(exc_info.value) == "Quota factor must be in the range of [0,1]"


def test_extend_reservations(project):
    assert project.extend_reservations("LabelingQueue") == 0
    assert project.extend_reservations("ReviewQueue") == 0
    with pytest.raises(InvalidQueryError):
        project.extend_reservations("InvalidQueueType")


@pytest.mark.skipif(condition=os.environ['LABELBOX_TEST_ENVIRON'] == "onprem",
                    reason="new mutation does not work for onprem")
def test_attach_instructions(client, project):
    with pytest.raises(ValueError) as execinfo:
        project.upsert_instructions('tests/integration/media/sample_pdf.pdf')
    assert str(
        execinfo.value
    ) == "Cannot attach instructions to a project that has not been set up."

    editor = list(
        client.get_labeling_frontends(
            where=LabelingFrontend.name == "editor"))[0]
    empty_ontology = {"tools": [], "classifications": []}
    project.setup(editor, empty_ontology)

    project.upsert_instructions('tests/integration/media/sample_pdf.pdf')
    time.sleep(3)
    assert project.ontology().normalized['projectInstructions'] is not None

    with pytest.raises(ValueError) as exc_info:
        project.upsert_instructions('/tmp/file.invalid_file_extension')
    assert "instructions_file must be a pdf or html file. Found" in str(
        exc_info.value)


@pytest.mark.skipif(condition=os.environ['LABELBOX_TEST_ENVIRON'] == "onprem",
                    reason="new mutation does not work for onprem")
def test_html_instructions(configured_project):
    html_file_path = '/tmp/instructions.html'
    sample_html_str = "<html></html>"

    with open(html_file_path, 'w') as file:
        file.write(sample_html_str)

    configured_project.upsert_instructions(html_file_path)
    updated_ontology = configured_project.ontology().normalized

    instructions = updated_ontology.pop('projectInstructions')
    assert requests.get(instructions).text == sample_html_str


@pytest.mark.skipif(condition=os.environ['LABELBOX_TEST_ENVIRON'] == "onprem",
                    reason="new mutation does not work for onprem")
def test_same_ontology_after_instructions(
        configured_project_with_complex_ontology):
    project, _ = configured_project_with_complex_ontology
    initial_ontology = project.ontology().normalized
    project.upsert_instructions('tests/assets/loremipsum.pdf')
    updated_ontology = project.ontology().normalized

    instructions = updated_ontology.pop('projectInstructions')

    assert initial_ontology == updated_ontology
    assert instructions is not None


def test_queued_data_row_export(configured_project):
    result = configured_project.export_queued_data_rows()
    assert len(result) == 1


def test_queue_mode(configured_project: Project):
    # ensures default queue mode is dataset
    assert configured_project.queue_mode == QueueMode.Dataset


def test_batches(batch_project: Project, dataset: Dataset, image_url):
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ] * 2)
    task.wait_till_done()
    data_rows = [dr.uid for dr in list(dataset.export_data_rows())]
    batch_one = f'batch one {uuid.uuid4()}'
    batch_two = f'batch two {uuid.uuid4()}'
    batch_project.create_batch(batch_one, [data_rows[0]])
    batch_project.create_batch(batch_two, [data_rows[1]])

    names = set([batch.name for batch in list(batch_project.batches())])
    assert names == {batch_one, batch_two}


@pytest.mark.parametrize('data_rows', [2], indirect=True)
def test_create_batch_with_global_keys_sync(batch_project: Project, data_rows):
    global_keys = [dr.global_key for dr in data_rows]
    batch_name = f'batch {uuid.uuid4()}'
    batch = batch_project.create_batch(batch_name, global_keys=global_keys)
    batch_data_rows = set(batch.export_data_rows())
    assert batch_data_rows == set(data_rows)


@pytest.mark.parametrize('data_rows', [2], indirect=True)
def test_create_batch_with_global_keys_async(batch_project: Project, data_rows):
    global_keys = [dr.global_key for dr in data_rows]
    batch_name = f'batch {uuid.uuid4()}'
    batch = batch_project._create_batch_async(batch_name,
                                              global_keys=global_keys)
    batch_data_rows = set(batch.export_data_rows())
    assert batch_data_rows == set(data_rows)


def test_media_type(client, configured_project: Project, rand_gen):
    # Existing project with no media_type
    assert isinstance(configured_project.media_type, MediaType)

    # Update test
    project = client.create_project(name=rand_gen(str))
    project.update(media_type=MediaType.Image)
    assert project.media_type == MediaType.Image
    project.delete()

    for media_type in MediaType.get_supported_members():

        project = client.create_project(name=rand_gen(str),
                                        media_type=MediaType[media_type])
        assert project.media_type == MediaType[media_type]
        project.delete()
