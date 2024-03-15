import datetime
import pytest
import uuid

import labelbox as lb
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.schema.media_type import MediaType
import labelbox.types as lb_types
from labelbox.data.annotation_types.data import (
    AudioData,
    ConversationData,
    DicomData,
    DocumentData,
    HTMLData,
    ImageData,
    TextData,
    LlmPromptCreationData,
    LlmPromptResponseCreationData,
    LlmResponseCreationData,
)
from labelbox.data.serialization import NDJsonConverter
from labelbox.schema.annotation_import import AnnotationImportState

radio_annotation = lb_types.ClassificationAnnotation(
    name="radio",
    value=lb_types.Radio(answer=lb_types.ClassificationAnswer(
        name="second_radio_answer")),
)
checklist_annotation = lb_types.ClassificationAnnotation(
    name="checklist",
    value=lb_types.Checklist(answer=[
        lb_types.ClassificationAnswer(name="option1"),
        lb_types.ClassificationAnswer(name="option2"),
    ]),
)
text_annotation = lb_types.ClassificationAnnotation(
    name="text", value=lb_types.Text(answer="sample text"))

video_mask_annotation = lb_types.VideoMaskAnnotation(
    frames=[
        lb_types.MaskFrame(
            index=10,
            instance_uri=
            "https://storage.googleapis.com/labelbox-datasets/video-sample-data/mask_example.png",
        )
    ],
    instances=[
        lb_types.MaskInstance(color_rgb=(255, 255, 255),
                              name="segmentation_mask")
    ],
)

test_params = [
    [
        "html",
        lb_types.HTMLData,
        [radio_annotation, checklist_annotation, text_annotation],
    ],
    [
        "audio",
        lb_types.AudioData,
        [radio_annotation, checklist_annotation, text_annotation],
    ],
    ["video", lb_types.VideoData, [video_mask_annotation]],
]


def create_data_row_for_project(project, dataset, data_row_ndjson, batch_name):
    data_row = dataset.create_data_row(data_row_ndjson)

    project.create_batch(
        batch_name,
        [data_row.uid],  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids.append(data_row.uid)

    return data_row


def test_import_data_types_by_global_key(
    client,
    configured_project,
    initial_dataset,
    rand_gen,
    data_row_json_by_data_type,
    annotations_by_data_type,
    export_v2_test_helpers,
    helpers,
):
    project = configured_project
    project_id = project.uid
    dataset = initial_dataset
    data_type_class = ImageData
    helpers.set_project_media_type_from_data_type(project, data_type_class)

    data_row_ndjson = data_row_json_by_data_type["image"]
    data_row_ndjson["global_key"] = str(uuid.uuid4())
    data_row = create_data_row_for_project(project, dataset, data_row_ndjson,
                                           rand_gen(str))

    annotations_ndjson = annotations_by_data_type["image"]
    annotations_list = [
        label.annotations
        for label in NDJsonConverter.deserialize(annotations_ndjson)
    ]
    labels = [
        lb_types.Label(
            data={'global_key': data_row.global_key},
            annotations=annotations,
        ) for annotations in annotations_list
    ]

    def find_data_row(dr):
        return dr['data_row']['id'] == data_row.uid

    label_import = lb.LabelImport.create_from_objects(client, project_id,
                                                      f"test-import-image",
                                                      labels)
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0

    result = export_v2_test_helpers.run_project_export_v2_task(project)
    exported_data = list(filter(find_data_row, result))[0]
    assert exported_data

    label = exported_data['projects'][project.uid]['labels'][0]
    annotations = label['annotations']
    objects = annotations['objects']
    classifications = annotations['classifications']
    assert len(objects) + len(classifications) == len(labels)

    data_row.delete()


def validate_iso_format(date_string: str):
    parsed_t = datetime.datetime.fromisoformat(
        date_string)  # this will blow up if the string is not in iso format
    assert parsed_t.hour is not None
    assert parsed_t.minute is not None
    assert parsed_t.second is not None


@pytest.mark.parametrize(
    "data_type_class",
    [
        AudioData,
        HTMLData,
        ImageData,
        TextData,
        VideoData,
        ConversationData,
        DocumentData,
        DicomData,
        LlmPromptCreationData,
        LlmPromptResponseCreationData,
        LlmResponseCreationData,
    ],
)
def test_import_data_types_v2(
    client,
    configured_project,
    initial_dataset,
    data_row_json_by_data_type,
    annotations_by_data_type_v2,
    data_type_class,
    exports_v2_by_data_type,
    export_v2_test_helpers,
    rand_gen,
    helpers,
):
    project = configured_project
    dataset = initial_dataset
    project_id = project.uid

    helpers.set_project_media_type_from_data_type(project, data_type_class)

    data_type_string = data_type_class.__name__[:-4].lower()
    data_row_ndjson = data_row_json_by_data_type[data_type_string]
    data_row = create_data_row_for_project(project, dataset, data_row_ndjson,
                                           rand_gen(str))
    annotations_ndjson = annotations_by_data_type_v2[data_type_string]
    annotations_list = [
        label.annotations
        for label in NDJsonConverter.deserialize(annotations_ndjson)
    ]
    labels = [
        lb_types.Label(data={'uid': data_row.uid}, annotations=annotations)
        for annotations in annotations_list
    ]

    label_import = lb.LabelImport.create_from_objects(
        client, project_id, f"test-import-{data_type_string}", labels)
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0

    # TODO need to migrate project to the new BATCH mode and change this code
    # to be similar to tests/integration/test_task_queue.py

    result = export_v2_test_helpers.run_project_export_v2_task(project)

    exported_data = next(
        dr for dr in result if dr['data_row']['id'] == data_row.uid)
    assert exported_data

    # timestamp fields are in iso format
    validate_iso_format(exported_data["data_row"]["details"]["created_at"])
    validate_iso_format(exported_data["data_row"]["details"]["updated_at"])
    validate_iso_format(exported_data["projects"][project_id]["labels"][0]
                        ["label_details"]["created_at"])
    validate_iso_format(exported_data["projects"][project_id]["labels"][0]
                        ["label_details"]["updated_at"])

    assert exported_data["data_row"]["id"] == data_row.uid
    exported_project = exported_data["projects"][project_id]
    exported_project_labels = exported_project["labels"][0]
    exported_annotations = exported_project_labels["annotations"]

    helpers.remove_keys_recursive(exported_annotations,
                                  ["feature_id", "feature_schema_id"])
    helpers.rename_cuid_key_recursive(exported_annotations)
    assert exported_annotations == exports_v2_by_data_type[data_type_string]

    data_row = client.get_data_row(data_row.uid)
    data_row.delete()


@pytest.mark.parametrize("data_type, data_class, annotations", test_params)
@pytest.fixture
def one_datarow(client, rand_gen, data_row_json_by_data_type, data_type):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_json = data_row_json_by_data_type[data_type]
    data_row = dataset.create_data_row(data_row_json)

    yield data_row

    dataset.delete()


@pytest.fixture
def one_datarow_global_key(client, rand_gen, data_row_json_by_data_type):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row_json = data_row_json_by_data_type["video"]
    data_row = dataset.create_data_row(data_row_json)

    yield data_row

    dataset.delete()


@pytest.mark.parametrize("data_type, data_class, annotations", test_params)
def test_import_mal_annotations(
    client,
    configured_project_with_one_data_row,
    data_class,
    annotations,
    rand_gen,
    one_datarow,
    helpers,
):
    data_row = one_datarow
    helpers.set_project_media_type_from_data_type(
        configured_project_with_one_data_row, data_class)

    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        [data_row.uid],
    )

    labels = [
        lb_types.Label(data={'uid': data_row.uid}, annotations=annotations)
    ]

    import_annotations = lb.MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_with_one_data_row.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels,
    )
    import_annotations.wait_until_done()

    assert import_annotations.errors == []
    # MAL Labels cannot be exported and compared to input labels


def test_import_mal_annotations_global_key(client,
                                           configured_project_with_one_data_row,
                                           rand_gen, one_datarow_global_key,
                                           helpers):
    data_class = lb_types.VideoData
    data_row = one_datarow_global_key
    annotations = [video_mask_annotation]
    helpers.set_project_media_type_from_data_type(
        configured_project_with_one_data_row, data_class)

    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        [data_row.uid],
    )

    labels = [
        lb_types.Label(data={'global_key': data_row.global_key},
                       annotations=annotations)
    ]

    import_annotations = lb.MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_with_one_data_row.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels,
    )
    import_annotations.wait_until_done()

    assert import_annotations.errors == []
    # MAL Labels cannot be exported and compared to input labels
