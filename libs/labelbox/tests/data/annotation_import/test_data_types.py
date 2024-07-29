import pytest

from labelbox.data.annotation_types.data import (
    AudioData,
    ConversationData,
    DocumentData,
    HTMLData,
    ImageData,
    TextData,
)
from labelbox.data.serialization import NDJsonConverter
from labelbox.data.annotation_types.data.video import VideoData

import labelbox.types as lb_types
from labelbox.schema.media_type import MediaType

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
