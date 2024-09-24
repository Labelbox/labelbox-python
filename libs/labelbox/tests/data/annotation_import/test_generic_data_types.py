import datetime
from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.data.annotation_types import Label
import pytest
import uuid

import labelbox as lb
from labelbox.schema.media_type import MediaType
from labelbox.schema.annotation_import import AnnotationImportState
from labelbox import Project, Client, OntologyKind
import itertools

"""
 - integration test for importing mal labels and ground truths with each supported MediaType. 
 - NDJSON is used to generate annotations.
"""


def validate_iso_format(date_string: str):
    parsed_t = datetime.datetime.fromisoformat(
        date_string
    )  # this will blow up if the string is not in iso format
    assert parsed_t.hour is not None
    assert parsed_t.minute is not None
    assert parsed_t.second is not None


@pytest.mark.parametrize(
    "media_type, data_type_class",
    [
        (MediaType.Audio, GenericDataRowData),
        (MediaType.Html, GenericDataRowData),
        (MediaType.Image, GenericDataRowData),
        (MediaType.Text, GenericDataRowData),
        (MediaType.Video, GenericDataRowData),
        (MediaType.Conversational, GenericDataRowData),
        (MediaType.Document, GenericDataRowData),
        (MediaType.LLMPromptResponseCreation, GenericDataRowData),
        (MediaType.LLMPromptCreation, GenericDataRowData),
        (OntologyKind.ResponseCreation, GenericDataRowData),
        (OntologyKind.ModelEvaluation, GenericDataRowData),
    ],
)
def test_generic_data_row_type_by_data_row_id(
    media_type,
    data_type_class,
    annotations_by_media_type,
    hardcoded_datarow_id,
):
    annotations_ndjson = annotations_by_media_type[media_type]
    annotations_ndjson = [annotation[0] for annotation in annotations_ndjson]

    label = list(NDJsonConverter.deserialize(annotations_ndjson))[0]

    data_label = Label(
        data=data_type_class(uid=hardcoded_datarow_id()),
        annotations=label.annotations,
    )

    assert data_label.data.uid == label.data.uid
    assert label.annotations == data_label.annotations


@pytest.mark.parametrize(
    "media_type, data_type_class",
    [
        (MediaType.Audio, GenericDataRowData),
        (MediaType.Html, GenericDataRowData),
        (MediaType.Image, GenericDataRowData),
        (MediaType.Text, GenericDataRowData),
        (MediaType.Video, GenericDataRowData),
        (MediaType.Conversational, GenericDataRowData),
        (MediaType.Document, GenericDataRowData),
        # (MediaType.LLMPromptResponseCreation, GenericDataRowData),
        # (MediaType.LLMPromptCreation, GenericDataRowData),
        (OntologyKind.ResponseCreation, GenericDataRowData),
        (OntologyKind.ModelEvaluation, GenericDataRowData),
    ],
)
def test_generic_data_row_type_by_global_key(
    media_type,
    data_type_class,
    annotations_by_media_type,
    hardcoded_global_key,
):
    annotations_ndjson = annotations_by_media_type[media_type]
    annotations_ndjson = [annotation[0] for annotation in annotations_ndjson]

    label = list(NDJsonConverter.deserialize(annotations_ndjson))[0]

    data_label = Label(
        data=data_type_class(global_key=hardcoded_global_key()),
        annotations=label.annotations,
    )

    assert data_label.data.global_key == label.data.global_key
    assert label.annotations == data_label.annotations


@pytest.mark.parametrize(
    "configured_project, media_type",
    [
        (MediaType.Audio, MediaType.Audio),
        (MediaType.Html, MediaType.Html),
        (MediaType.Image, MediaType.Image),
        (MediaType.Text, MediaType.Text),
        (MediaType.Video, MediaType.Video),
        (MediaType.Conversational, MediaType.Conversational),
        (MediaType.Document, MediaType.Document),
        (MediaType.Dicom, MediaType.Dicom),
        (
            MediaType.LLMPromptResponseCreation,
            MediaType.LLMPromptResponseCreation,
        ),
        (MediaType.LLMPromptCreation, MediaType.LLMPromptCreation),
        (OntologyKind.ResponseCreation, OntologyKind.ResponseCreation),
        (OntologyKind.ModelEvaluation, OntologyKind.ModelEvaluation),
    ],
    indirect=["configured_project"],
)
def test_import_media_types(
    client: Client,
    configured_project: Project,
    annotations_by_media_type,
    exports_v2_by_media_type,
    export_v2_test_helpers,
    helpers,
    media_type,
):
    annotations_ndjson = list(
        itertools.chain.from_iterable(annotations_by_media_type[media_type])
    )

    label_import = lb.LabelImport.create_from_objects(
        client,
        configured_project.uid,
        f"test-import-{media_type}",
        annotations_ndjson,
    )
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0

    result = export_v2_test_helpers.run_project_export_v2_task(
        configured_project
    )

    assert result

    for exported_data in result:
        # timestamp fields are in iso format
        validate_iso_format(exported_data["data_row"]["details"]["created_at"])
        validate_iso_format(exported_data["data_row"]["details"]["updated_at"])
        validate_iso_format(
            exported_data["projects"][configured_project.uid]["labels"][0][
                "label_details"
            ]["created_at"]
        )
        validate_iso_format(
            exported_data["projects"][configured_project.uid]["labels"][0][
                "label_details"
            ]["updated_at"]
        )

        assert (
            exported_data["data_row"]["id"] in configured_project.data_row_ids
        )
        exported_project = exported_data["projects"][configured_project.uid]
        exported_project_labels = exported_project["labels"][0]
        exported_annotations = exported_project_labels["annotations"]

        expected_data = exports_v2_by_media_type[media_type]
        helpers.remove_keys_recursive(
            exported_annotations, ["feature_id", "feature_schema_id"]
        )
        helpers.rename_cuid_key_recursive(exported_annotations)

        assert exported_annotations == expected_data


@pytest.mark.parametrize(
    "configured_project_by_global_key, media_type",
    [
        (MediaType.Audio, MediaType.Audio),
        (MediaType.Html, MediaType.Html),
        (MediaType.Image, MediaType.Image),
        (MediaType.Text, MediaType.Text),
        (MediaType.Video, MediaType.Video),
        (MediaType.Conversational, MediaType.Conversational),
        (MediaType.Document, MediaType.Document),
        (MediaType.Dicom, MediaType.Dicom),
        (OntologyKind.ResponseCreation, OntologyKind.ResponseCreation),
        (OntologyKind.ModelEvaluation, OntologyKind.ModelEvaluation),
    ],
    indirect=["configured_project_by_global_key"],
)
def test_import_media_types_by_global_key(
    client,
    configured_project_by_global_key,
    annotations_by_media_type,
    exports_v2_by_media_type,
    export_v2_test_helpers,
    helpers,
    media_type,
):
    annotations_ndjson = list(
        itertools.chain.from_iterable(annotations_by_media_type[media_type])
    )

    label_import = lb.LabelImport.create_from_objects(
        client,
        configured_project_by_global_key.uid,
        f"test-import-{media_type}",
        annotations_ndjson,
    )
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0

    result = export_v2_test_helpers.run_project_export_v2_task(
        configured_project_by_global_key
    )

    assert result

    for exported_data in result:
        # timestamp fields are in iso format
        validate_iso_format(exported_data["data_row"]["details"]["created_at"])
        validate_iso_format(exported_data["data_row"]["details"]["updated_at"])
        validate_iso_format(
            exported_data["projects"][configured_project_by_global_key.uid][
                "labels"
            ][0]["label_details"]["created_at"]
        )
        validate_iso_format(
            exported_data["projects"][configured_project_by_global_key.uid][
                "labels"
            ][0]["label_details"]["updated_at"]
        )

        assert (
            exported_data["data_row"]["id"]
            in configured_project_by_global_key.data_row_ids
        )
        exported_project = exported_data["projects"][
            configured_project_by_global_key.uid
        ]
        exported_project_labels = exported_project["labels"][0]
        exported_annotations = exported_project_labels["annotations"]

        expected_data = exports_v2_by_media_type[media_type]
        helpers.remove_keys_recursive(
            exported_annotations, ["feature_id", "feature_schema_id"]
        )
        helpers.rename_cuid_key_recursive(exported_annotations)

        assert exported_annotations == expected_data


@pytest.mark.parametrize(
    "configured_project, media_type",
    [
        (MediaType.Audio, MediaType.Audio),
        (MediaType.Html, MediaType.Html),
        (MediaType.Image, MediaType.Image),
        (MediaType.Text, MediaType.Text),
        (MediaType.Video, MediaType.Video),
        (MediaType.Conversational, MediaType.Conversational),
        (MediaType.Document, MediaType.Document),
        (MediaType.Dicom, MediaType.Dicom),
        (
            MediaType.LLMPromptResponseCreation,
            MediaType.LLMPromptResponseCreation,
        ),
        (MediaType.LLMPromptCreation, MediaType.LLMPromptCreation),
        (OntologyKind.ResponseCreation, OntologyKind.ResponseCreation),
        (OntologyKind.ModelEvaluation, OntologyKind.ModelEvaluation),
    ],
    indirect=["configured_project"],
)
def test_import_mal_annotations(
    client, configured_project: Project, annotations_by_media_type, media_type
):
    annotations_ndjson = list(
        itertools.chain.from_iterable(annotations_by_media_type[media_type])
    )

    import_annotations = lb.MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=annotations_ndjson,
    )
    import_annotations.wait_until_done()

    assert import_annotations.errors == []
    # MAL Labels cannot be exported and compared to input labels


@pytest.mark.parametrize(
    "configured_project_by_global_key, media_type",
    [
        (MediaType.Audio, MediaType.Audio),
        (MediaType.Html, MediaType.Html),
        (MediaType.Image, MediaType.Image),
        (MediaType.Text, MediaType.Text),
        (MediaType.Video, MediaType.Video),
        (MediaType.Conversational, MediaType.Conversational),
        (MediaType.Document, MediaType.Document),
        (MediaType.Dicom, MediaType.Dicom),
        (OntologyKind.ResponseCreation, OntologyKind.ResponseCreation),
        (OntologyKind.ModelEvaluation, OntologyKind.ModelEvaluation),
    ],
    indirect=["configured_project_by_global_key"],
)
def test_import_mal_annotations_global_key(
    client,
    configured_project_by_global_key: Project,
    annotations_by_media_type,
    media_type,
):
    annotations_ndjson = list(
        itertools.chain.from_iterable(annotations_by_media_type[media_type])
    )

    import_annotations = lb.MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_by_global_key.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=annotations_ndjson,
    )
    import_annotations.wait_until_done()

    assert import_annotations.errors == []
    # MAL Labels cannot be exported and compared to input labels
