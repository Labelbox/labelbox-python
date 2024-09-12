from email import message
import pytest
from pydantic import ValidationError

from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.label import Label


def test_generic_data_type():
    data = {
        "global_key": "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr",
    }
    label = Label(data=data)
    data = label.data
    assert isinstance(data, GenericDataRowData)
    assert (
        data.global_key
        == "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr"
    )


def test_generic_data_type_validations():
    data = {
        "row_data": "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr",
    }
    with pytest.raises(ValueError, match="Exactly one of"):
        Label(data=data)

    data = {
        "uid": "abcd",
        "global_key": "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr",
    }
    with pytest.raises(ValueError, match="Only one of"):
        Label(data=data)


def test_video_data_type():
    data = {
        "global_key": "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr",
    }
    with pytest.warns(UserWarning, match="Use a dict"):
        label = Label(data=VideoData(**data))
    data = label.data
    assert isinstance(data, VideoData)
    assert (
        data.global_key
        == "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr"
    )


def test_generic_data_row():
    data = {
        "global_key": "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr",
    }
    label = Label(data=GenericDataRowData(**data))
    data = label.data
    assert isinstance(data, GenericDataRowData)
    assert (
        data.global_key
        == "https://lb-test-data.s3.us-west-1.amazonaws.com/image-samples/sample-image-1.jpg-BEidMVWRmyXjVCnr"
    )
