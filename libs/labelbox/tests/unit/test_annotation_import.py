import pytest

from labelbox.schema.annotation_import import AnnotationImport


def test_data_row_validation_errors():
    predictions = [
        {
            "answer": {
                "schemaId": "ckrb1sfl8099g0y91cxbd5ftb",
            },
            "schemaId": "c123",
            "dataRow": {"globalKey": "05e8ee85-072e-4eb2-b30a-501dee9b0d9d"},
        },
        {
            "answer": {
                "schemaId": "ckrb1sfl8099g0y91cxbd5ftb",
            },
            "schemaId": "c123",
            "dataRow": {"globalKey": "05e8ee85-072e-4eb2-b30a-501dee9b0d9d"},
        },
        {
            "answer": {
                "schemaId": "ckrb1sfl8099g0y91cxbd5ftb",
            },
            "schemaId": "c123",
            "dataRow": {"globalKey": "05e8ee85-072e-4eb2-b30a-501dee9b0d9d"},
        },
        {
            "answer": {
                "schemaId": "ckrb1sfl8099g0y91cxbd5ftb",
            },
            "schemaId": "c123",
            "dataRow": {"globalKey": "05e8ee85-072e-4eb2-b30a-501dee9b0d9d"},
        },
        {
            "answer": {
                "schemaId": "ckrb1sfl8099g0y91cxbd5ftb",
            },
            "schemaId": "c123",
            "dataRow": {"globalKey": "05e8ee85-072e-4eb2-b30a-501dee9b0d9d"},
        },
    ]

    # Set up data for validation errors
    # Invalid: Remove 'dataRow' part entirely
    del predictions[0]["dataRow"]

    # Invalid: Set both id and globalKey
    predictions[1]["dataRow"] = {
        "id": "some id",
        "globalKey": "some global key",
    }

    # Invalid: Set both id and globalKey to None
    predictions[2]["dataRow"] = {"id": None, "globalKey": None}

    # Valid
    predictions[3]["dataRow"] = {
        "id": "some id",
    }

    # Valid
    predictions[4]["dataRow"] = {
        "globalKey": "some global key",
    }

    with pytest.raises(ValueError) as exc_info:
        AnnotationImport._validate_data_rows(predictions)
    exception_str = str(exc_info.value)
    assert "Found 3 annotations with errors" in exception_str
    assert "'dataRow' is missing in" in exception_str
    assert (
        "Must provide only one of 'id' or 'globalKey' for 'dataRow'"
        in exception_str
    )
    assert (
        "'dataRow': {'id': 'some id', 'globalKey': 'some global key'}"
        in exception_str
    )
    assert "'dataRow': {'id': None, 'globalKey': None}" in exception_str
