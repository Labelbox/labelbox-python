import time
import os
import uuid
import pytest
import requests

from labelbox import Project, LabelingFrontend, Dataset
from labelbox.exceptions import InvalidQueryError
from labelbox.schema.media_type import MediaType
from labelbox.schema.quality_mode import QualityMode
from labelbox.schema.queue_mode import QueueMode


def test_project(client, rand_gen):
    data = {
        "name": rand_gen(str),
        "description": rand_gen(str),
        "queue_mode": QueueMode.Batch.Batch,
        "media_type": MediaType.Image,
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
    projects = list(client.get_projects(where=(Project.uid == project.uid)))

    assert project not in projects


@pytest.fixture
def data_for_project_test(client, rand_gen):
    projects = []

    def _create_project(name: str = None):
        if name is None:
            name = rand_gen(str)
        project = client.create_project(name=name)
        projects.append(project)
        return project

    yield _create_project

    for project in projects:
        project.delete()


def test_update_project_resource_tags(client, rand_gen, data_for_project_test):
    p1 = data_for_project_test()

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

    org = client.get_organization()
    assert org.uid is not None

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

    project_resource_tags = client.get_project(p1.uid).get_resource_tags()
    assert len(project_resource_tags) == 1
    assert project_resource_tags[0].uid == tagA.uid

    delete_tag(tagA.uid)
    delete_tag(tagB.uid)


def test_project_filtering(client, rand_gen, data_for_project_test):
    name_1 = rand_gen(str)
    p1 = data_for_project_test(name_1)
    name_2 = rand_gen(str)
    p2 = data_for_project_test(name_2)

    assert list(client.get_projects(where=Project.name == name_1)) == [p1]
    assert list(client.get_projects(where=Project.name == name_2)) == [p2]


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
def test_html_instructions(project_with_empty_ontology):
    html_file_path = '/tmp/instructions.html'
    sample_html_str = "<html></html>"

    with open(html_file_path, 'w') as file:
        file.write(sample_html_str)

    project_with_empty_ontology.upsert_instructions(html_file_path)
    updated_ontology = project_with_empty_ontology.ontology().normalized

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


def test_batches(project: Project, dataset: Dataset, image_url):
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ] * 2)
    task.wait_till_done()
    export_task = dataset.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()
    data_rows = [dr.json["data_row"]["id"] for dr in stream]
    batch_one = f'batch one {uuid.uuid4()}'
    batch_two = f'batch two {uuid.uuid4()}'
    project.create_batch(batch_one, [data_rows[0]])
    project.create_batch(batch_two, [data_rows[1]])

    names = set([batch.name for batch in list(project.batches())])
    assert names == {batch_one, batch_two}


@pytest.mark.parametrize('data_rows', [2], indirect=True)
def test_create_batch_with_global_keys_sync(project: Project, data_rows):
    global_keys = [dr.global_key for dr in data_rows]
    batch_name = f'batch {uuid.uuid4()}'
    batch = project.create_batch(batch_name, global_keys=global_keys)

    assert batch.size == len(set(data_rows))


@pytest.mark.parametrize('data_rows', [2], indirect=True)
def test_create_batch_with_global_keys_async(project: Project, data_rows):
    global_keys = [dr.global_key for dr in data_rows]
    batch_name = f'batch {uuid.uuid4()}'
    batch = project._create_batch_async(batch_name, global_keys=global_keys)

    assert batch.size == len(set(data_rows))


def test_media_type(client, project: Project, rand_gen):
    # Existing project with no media_type
    assert isinstance(project.media_type, MediaType)

    # Update test
    project = client.create_project(name=rand_gen(str))
    project.update(media_type=MediaType.Image)
    assert project.media_type == MediaType.Image
    project.delete()

    for media_type in MediaType.get_supported_members():
        # Exclude LLM media types for now, as they are not supported
        if MediaType[media_type] in [
                MediaType.LLMPromptCreation,
                MediaType.LLMPromptResponseCreation, MediaType.LLM
        ]:
            continue

        project = client.create_project(name=rand_gen(str),
                                        media_type=MediaType[media_type])
        assert project.media_type == MediaType[media_type]
        project.delete()


def test_queue_mode(client, rand_gen):
    project = client.create_project(name=rand_gen(str))  # defaults to benchmark and consensus
    assert project.auto_audit_number_of_labels == 3
    assert project.auto_audit_percentage == 0

    project = client.create_project(name=rand_gen(str), quality_modes=[QualityMode.Benchmark])
    assert project.auto_audit_number_of_labels == 1
    assert project.auto_audit_percentage == 1

    project = client.create_project(
        name=rand_gen(str), quality_modes=[QualityMode.Benchmark, QualityMode.Consensus]
    )
    assert project.auto_audit_number_of_labels == 3
    assert project.auto_audit_percentage == 0


def test_label_count(client, configured_batch_project_with_label):
    project = client.create_project(name="test label count")
    assert project.get_label_count() == 0
    project.delete()

    [source_project, _, _, _] = configured_batch_project_with_label
    num_labels = sum([1 for _ in source_project.labels()])
    assert source_project.get_label_count() == num_labels


def test_clone(client, project, rand_gen):
    # cannot clone unknown project media type
    project = client.create_project(name=rand_gen(str),
                                    media_type=MediaType.Image)
    cloned_project = project.clone()

    assert cloned_project.description == project.description
    assert cloned_project.media_type == project.media_type
    assert cloned_project.queue_mode == project.queue_mode
    assert cloned_project.auto_audit_number_of_labels == project.auto_audit_number_of_labels
    assert cloned_project.auto_audit_percentage == project.auto_audit_percentage
    assert cloned_project.get_label_count() == 0

    project.delete()
    cloned_project.delete()
