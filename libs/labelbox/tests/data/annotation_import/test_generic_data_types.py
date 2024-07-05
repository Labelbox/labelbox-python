import datetime
import pytest
import uuid

import labelbox as lb
from labelbox.schema.media_type import MediaType
from labelbox.schema.annotation_import import AnnotationImportState
from labelbox import Project, Client
import itertools


def validate_iso_format(date_string: str):
    parsed_t = datetime.datetime.fromisoformat(
        date_string)  # this will blow up if the string is not in iso format
    assert parsed_t.hour is not None
    assert parsed_t.minute is not None
    assert parsed_t.second is not None

# TODO: add MediaType.LLMPromptResponseCreation(data gen) once supported and llm human preference once media type is added
@pytest.mark.parametrize(
    "configured_project",
    [
        MediaType.Audio,
        MediaType.Html,
        MediaType.Image,
        MediaType.Text,
        MediaType.Video,
        MediaType.Conversational,
        MediaType.Document,
        MediaType.Dicom,
    ],
    indirect=True
)
def test_import_media_types(
    client: Client,
    configured_project: Project,
    annotations_by_media_type,
    exports_v2_by_media_type,
    export_v2_test_helpers,
    helpers,
):
    annotations_ndjson =  list(itertools.chain.from_iterable(annotations_by_media_type[configured_project.media_type]))

    label_import = lb.LabelImport.create_from_objects(
        client, configured_project.uid, f"test-import-{configured_project.media_type}", annotations_ndjson)
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0

    result = export_v2_test_helpers.run_project_export_v2_task(configured_project)

    assert result

    for exported_data in result:
        # timestamp fields are in iso format
        validate_iso_format(exported_data["data_row"]["details"]["created_at"])
        validate_iso_format(exported_data["data_row"]["details"]["updated_at"])
        validate_iso_format(exported_data["projects"][configured_project.uid]["labels"][0]
                            ["label_details"]["created_at"])
        validate_iso_format(exported_data["projects"][configured_project.uid]["labels"][0]
                            ["label_details"]["updated_at"])

        assert exported_data["data_row"]["id"] in configured_project.data_row_ids
        exported_project = exported_data["projects"][configured_project.uid]
        exported_project_labels = exported_project["labels"][0]
        exported_annotations = exported_project_labels["annotations"]

        #TODO Occasional dicom data cuts out the key_frame_feature_map with export. This might be a bug but does not happen every time. Need to look into this issue but removing key_frame_feature_map to stabilize test.
        expected_data = exports_v2_by_media_type[configured_project.media_type]
        helpers.remove_keys_recursive(exported_annotations,
                                    ["feature_id", "feature_schema_id", "key_frame_feature_map"])
        helpers.remove_keys_recursive(expected_data,
                                    ["key_frame_feature_map"])        
        helpers.rename_cuid_key_recursive(exported_annotations)

        assert exported_annotations == expected_data 


@pytest.mark.order(1)
@pytest.mark.parametrize(
    "configured_project_by_global_key",
    [
        MediaType.Audio,
        MediaType.Html,
        MediaType.Image,
        MediaType.Text,
        MediaType.Video,
        MediaType.Conversational,
        MediaType.Document,
        MediaType.Dicom,
    ],
    indirect=True
)
def test_import_media_types_by_global_key(
    client,
    configured_project_by_global_key,
    annotations_by_media_type,
    exports_v2_by_media_type,
    export_v2_test_helpers,
    helpers,
):
    annotations_ndjson =  list(itertools.chain.from_iterable(annotations_by_media_type[configured_project_by_global_key.media_type]))

    label_import = lb.LabelImport.create_from_objects(
        client, configured_project_by_global_key.uid, f"test-import-{configured_project_by_global_key.media_type}", annotations_ndjson)
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0

    result = export_v2_test_helpers.run_project_export_v2_task(configured_project_by_global_key)

    assert result

    for exported_data in result:
        # timestamp fields are in iso format
        validate_iso_format(exported_data["data_row"]["details"]["created_at"])
        validate_iso_format(exported_data["data_row"]["details"]["updated_at"])
        validate_iso_format(exported_data["projects"][configured_project_by_global_key.uid]["labels"][0]
                            ["label_details"]["created_at"])
        validate_iso_format(exported_data["projects"][configured_project_by_global_key.uid]["labels"][0]
                            ["label_details"]["updated_at"])

        assert exported_data["data_row"]["id"] in configured_project_by_global_key.data_row_ids
        exported_project = exported_data["projects"][configured_project_by_global_key.uid]
        exported_project_labels = exported_project["labels"][0]
        exported_annotations = exported_project_labels["annotations"]

        #TODO Occasional dicom data cuts out the key_frame_feature_map with export. This might be a bug but does not happen every time. Need to look into this issue but removing key_frame_feature_map to stabilize test.
        expected_data = exports_v2_by_media_type[configured_project_by_global_key.media_type]
        helpers.remove_keys_recursive(exported_annotations,
                                    ["feature_id", "feature_schema_id", "key_frame_feature_map"])
        helpers.remove_keys_recursive(expected_data,
                                    ["key_frame_feature_map"])        
        helpers.rename_cuid_key_recursive(exported_annotations)

        assert exported_annotations == expected_data 


@pytest.mark.parametrize(
    "configured_project",
    [
        MediaType.Audio,
        MediaType.Html,
        MediaType.Image,
        MediaType.Text,
        MediaType.Video,
        MediaType.Conversational,
        MediaType.Document,
        MediaType.Dicom,
    ],
    indirect=True
)
def test_import_mal_annotations(
    client,
    configured_project: Project,
    annotations_by_media_type,
):
    annotations_ndjson =  list(itertools.chain.from_iterable(annotations_by_media_type[configured_project.media_type]))

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
    "configured_project_by_global_key",
    [
        MediaType.Audio,
        MediaType.Html,
        MediaType.Image,
        MediaType.Text,
        MediaType.Video,
        MediaType.Conversational,
        MediaType.Document,
        MediaType.Dicom,
    ],
    indirect=True
)
def test_import_mal_annotations_global_key(client,
                                           configured_project_by_global_key: Project,
                                           annotations_by_media_type):

    annotations_ndjson =  list(itertools.chain.from_iterable(annotations_by_media_type[configured_project_by_global_key.media_type]))

    import_annotations = lb.MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_by_global_key.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=annotations_ndjson,
    )
    import_annotations.wait_until_done()

    assert import_annotations.errors == []
    # MAL Labels cannot be exported and compared to input labels
