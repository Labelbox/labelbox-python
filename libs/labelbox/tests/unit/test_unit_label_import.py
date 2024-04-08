import uuid
import pytest
from unittest.mock import MagicMock, patch

from labelbox.schema.annotation_import import LabelImport, logger


def test_should_warn_user_about_unsupported_confidence():
    """this test should check running state only to validate running, not completed"""
    id = str(uuid.uuid4())

    labels = [
        {
            "uuid": "b862c586-8614-483c-b5e6-82810f70cac0",
            "schemaId": "ckrazcueb16og0z6609jj7y3y",
            "dataRow": {
                "id": "ckrazctum0z8a0ybc0b0o0g0v"
            },
            "confidence": 0.851,
            "bbox": {
                "top": 1352,
                "left": 2275,
                "height": 350,
                "width": 139
            }
        },
    ]
    with patch.object(LabelImport, '_create_label_import_from_bytes'):
        with patch.object(logger, 'warning') as warning_mock:
            LabelImport.create_from_objects(client=MagicMock(),
                                            project_id=id,
                                            name=id,
                                            labels=labels)
            warning_mock.assert_called_once()
            "Confidence scores are not supported in Label Import" in warning_mock.call_args_list[
                0].args[0]


def test_invalid_labels_format():
    """this test should confirm that labels are required to be in a form of list"""
    id = str(uuid.uuid4())

    label = {
        "uuid": "b862c586-8614-483c-b5e6-82810f70cac0",
        "schemaId": "ckrazcueb16og0z6609jj7y3y",
        "dataRow": {
            "id": "ckrazctum0z8a0ybc0b0o0g0v"
        },
        "bbox": {
            "top": 1352,
            "left": 2275,
            "height": 350,
            "width": 139
        }
    }
    with patch.object(LabelImport, '_create_label_import_from_bytes'):
        with pytest.raises(TypeError):
            LabelImport.create_from_objects(client=MagicMock(),
                                            project_id=id,
                                            name=id,
                                            labels=label)
