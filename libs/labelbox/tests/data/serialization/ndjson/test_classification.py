import json

from labelbox.data.annotation_types.classification.classification import (
    Checklist,
    Radio,
    Text,
)
from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.serialization.ndjson.converter import NDJsonConverter

from labelbox.types import (
    Label,
    ClassificationAnnotation,
    ClassificationAnswer,
)
from labelbox.data.mixins import CustomMetric


def test_classification():
    with open(
        "tests/data/assets/ndjson/classification_import.json", "r"
    ) as file:
        data = json.load(file)

    label = Label(
        data=GenericDataRowData(
            uid="ckrb1sf1i1g7i0ybcdc6oc8ct",
        ),
        annotations=[
            ClassificationAnnotation(
                feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                value=Radio(
                    answer=ClassificationAnswer(
                        custom_metrics=[
                            CustomMetric(name="customMetric1", value=0.5),
                            CustomMetric(name="customMetric2", value=0.3),
                        ],
                        confidence=0.8,
                        feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                    ),
                ),
            ),
            ClassificationAnnotation(
                feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                value=Checklist(
                    answer=[
                        ClassificationAnswer(
                            custom_metrics=[
                                CustomMetric(name="customMetric1", value=0.5),
                                CustomMetric(name="customMetric2", value=0.3),
                            ],
                            confidence=0.82,
                            feature_schema_id="ckrb1sfl8099e0y919v260awv",
                        )
                    ],
                ),
            ),
            ClassificationAnnotation(
                feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                extra={"uuid": "78ff6a23-bebe-475c-8f67-4c456909648f"},
                value=Text(answer="a value"),
            ),
        ],
    )

    res = list(NDJsonConverter.serialize([label]))
    assert res == data


def test_classification_with_name():
    with open(
        "tests/data/assets/ndjson/classification_import_name_only.json", "r"
    ) as file:
        data = json.load(file)
    label = Label(
        data=GenericDataRowData(
            uid="ckrb1sf1i1g7i0ybcdc6oc8ct",
        ),
        annotations=[
            ClassificationAnnotation(
                name="classification a",
                extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                value=Radio(
                    answer=ClassificationAnswer(
                        custom_metrics=[
                            CustomMetric(name="customMetric1", value=0.5),
                            CustomMetric(name="customMetric2", value=0.3),
                        ],
                        confidence=0.99,
                        name="choice 1",
                    ),
                ),
            ),
            ClassificationAnnotation(
                name="classification b",
                extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                value=Checklist(
                    answer=[
                        ClassificationAnswer(
                            custom_metrics=[
                                CustomMetric(name="customMetric1", value=0.5),
                                CustomMetric(name="customMetric2", value=0.3),
                            ],
                            confidence=0.945,
                            name="choice 2",
                        )
                    ],
                ),
            ),
            ClassificationAnnotation(
                name="classification c",
                extra={"uuid": "150d60de-30af-44e4-be20-55201c533312"},
                value=Text(answer="a value"),
            ),
        ],
    )

    res = list(NDJsonConverter.serialize([label]))
    assert res == data
