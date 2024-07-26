import datetime
from labelbox.schema.label import Label
import pytest
import uuid

from labelbox.data.annotation_types.data import (
    AudioData,
    ConversationData,
    DicomData,
    DocumentData,
    HTMLData,
    ImageData,
    TextData,
)
from labelbox.data.serialization import NDJsonConverter
from labelbox.data.annotation_types.data.video import VideoData

import labelbox as lb
import labelbox.types as lb_types
from labelbox.schema.media_type import MediaType
from labelbox.schema.annotation_import import AnnotationImportState
from labelbox import Project, Client

# Unit test for label based on data type.
# TODO: Dicom removed it is unstable when you deserialize and serialize on label import. If we intend to keep this library this needs add generic data types tests work with this data type.
# TODO: add MediaType.LLMPromptResponseCreation(data gen) once supported and llm human preference once media type is added


@pytest.mark.parametrize(
    "media_type, data_type_class",
    [
        (MediaType.Audio, AudioData),
        (MediaType.Html, HTMLData),
        (MediaType.Image, ImageData),
        (MediaType.Text, TextData),
        (MediaType.Video, VideoData),
        (MediaType.Conversational, ConversationData),
        (MediaType.Document, DocumentData),
    ],
)
def test_data_row_type_by_data_row_id(
    media_type,
    data_type_class,
    annotations_by_media_type,
    hardcoded_datarow_id,
):
    annotations_ndjson =  annotations_by_media_type[media_type]
    annotations_ndjson = [annotation[0] for annotation in annotations_ndjson]
    
    label = list(NDJsonConverter.deserialize(annotations_ndjson))[0]
   
    data_label = lb_types.Label(data=data_type_class(uid = hardcoded_datarow_id()),
                       annotations=label.annotations)

    assert data_label.data.uid == label.data.uid
    assert label.annotations == data_label.annotations


@pytest.mark.parametrize(
    "media_type, data_type_class",
    [
        (MediaType.Audio, AudioData),
        (MediaType.Html, HTMLData),
        (MediaType.Image, ImageData),
        (MediaType.Text, TextData),
        (MediaType.Video, VideoData),
        (MediaType.Conversational, ConversationData),
        (MediaType.Document, DocumentData),
    ],
)
def test_data_row_type_by_global_key(
    media_type,
    data_type_class,
    annotations_by_media_type,
    hardcoded_global_key,
):
    annotations_ndjson =  annotations_by_media_type[media_type]
    annotations_ndjson = [annotation[0] for annotation in annotations_ndjson]
    
    label = list(NDJsonConverter.deserialize(annotations_ndjson))[0]
   
    data_label = lb_types.Label(data=data_type_class(global_key = hardcoded_global_key()),
                       annotations=label.annotations)

    assert data_label.data.global_key == label.data.global_key
    assert label.annotations == data_label.annotations


@pytest.mark.parametrize("_, data_class, annotations", test_params)
def test_import_label_annotations_with_is_benchmark_reference_flag(
        data_class, annotations, _):
    labels = [
        lb_types.Label(data=data_class(uid=str(uuid.uuid4()),
                                       url="http://test.com"),
                       annotations=annotations,
                       is_benchmark_reference=True)
    ]
    serialized_annotations = get_annotation_comparison_dicts_from_labels(labels)

    assert len(serialized_annotations) == len(annotations)
    for serialized_annotation in serialized_annotations:
        assert serialized_annotation["isBenchmarkReferenceLabel"]

