from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import (
    Label,
    ClassificationAnnotation,
    Radio,
    ClassificationAnswer,
)


def test_generic_data_row_global_key_included():
    expected = [
        {
            "answer": {"schemaId": "ckrb1sfl8099g0y91cxbd5ftb"},
            "dataRow": {"globalKey": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
            "schemaId": "ckrb1sfjx099a0y914hl319ie",
            "uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673",
        }
    ]

    label = Label(
        data=GenericDataRowData(
            global_key="ckrb1sf1i1g7i0ybcdc6oc8ct",
        ),
        annotations=[
            ClassificationAnnotation(
                feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                value=Radio(
                    answer=ClassificationAnswer(
                        feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                    ),
                ),
            )
        ],
    )

    res = list(NDJsonConverter.serialize([label]))

    assert res == expected


def test_dict_data_row_global_key_included():
    expected = [
        {
            "answer": {"schemaId": "ckrb1sfl8099g0y91cxbd5ftb"},
            "dataRow": {"globalKey": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
            "schemaId": "ckrb1sfjx099a0y914hl319ie",
            "uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673",
        }
    ]

    label = Label(
        data={
            "global_key": "ckrb1sf1i1g7i0ybcdc6oc8ct",
        },
        annotations=[
            ClassificationAnnotation(
                feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                value=Radio(
                    answer=ClassificationAnswer(
                        feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                    ),
                ),
            )
        ],
    )

    res = list(NDJsonConverter.serialize([label]))

    assert res == expected
