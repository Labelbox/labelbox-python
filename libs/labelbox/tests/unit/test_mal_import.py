import uuid
import pytest
from unittest.mock import MagicMock, patch

from labelbox.schema.annotation_import import MALPredictionImport, logger


def test_should_warn_user_about_unsupported_confidence():
    """this test should check running state only to validate running, not completed"""
    id = str(uuid.uuid4())

    labels = [
        {
            "bbox": {"height": 428, "left": 2089, "top": 1251, "width": 158},
            "classifications": [
                {
                    "answer": [
                        {
                            "schemaId": "ckrb1sfl8099e0y919v260awv",
                            "confidence": 0.894,
                        }
                    ],
                    "schemaId": "ckrb1sfkn099c0y910wbo0p1a",
                }
            ],
            "dataRow": {"id": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
            "schemaId": "ckrb1sfjx099a0y914hl319ie",
            "uuid": "d009925d-91a3-4f67-abd9-753453f5a584",
        },
    ]
    with patch.object(MALPredictionImport, "_create_mal_import_from_bytes"):
        with patch.object(logger, "warning") as warning_mock:
            MALPredictionImport.create_from_objects(
                client=MagicMock(), project_id=id, name=id, predictions=labels
            )
            warning_mock.assert_called_once()
            "Confidence scores are not supported in MAL Prediction Import" in warning_mock.call_args_list[
                0
            ].args[0]


def test_invalid_labels_format():
    """this test should confirm that annotations are required to be in a form of list"""
    id = str(uuid.uuid4())

    label = {
        "bbox": {"height": 428, "left": 2089, "top": 1251, "width": 158},
        "classifications": [
            {
                "answer": [
                    {
                        "schemaId": "ckrb1sfl8099e0y919v260awv",
                        "confidence": 0.894,
                    }
                ],
                "schemaId": "ckrb1sfkn099c0y910wbo0p1a",
            }
        ],
        "dataRow": {"id": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
        "schemaId": "ckrb1sfjx099a0y914hl319ie",
        "uuid": "3a83db52-75e0-49af-a171-234ce604502a",
    }

    with patch.object(MALPredictionImport, "_create_mal_import_from_bytes"):
        with pytest.raises(TypeError):
            MALPredictionImport.create_from_objects(
                client=MagicMock(), project_id=id, name=id, predictions=label
            )


def test_external_id_import_raises_value_error():
    import labelbox.data.annotation_types as lb_types
    from labelbox import MALPredictionImport

    id = str(uuid.uuid4())
    bbox_annotation = lb_types.ObjectAnnotation(
        name="something",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=100, y=100),
            end=lb_types.Point(x=200, y=200)
        )
    )
    labels = [
        lb_types.Label(
            data={"external_id": "name.jpg"},
            annotations=[bbox_annotation]
        )
    ]
    with pytest.raises(ValueError) as excinfo:
        MALPredictionImport.create_from_objects(
            client=MagicMock(),
            project_id=id,
            name=id,
            predictions=labels
        )
    assert "NDJSON serialization/import does not support referencing data rows by external_id" in str(excinfo.value)

