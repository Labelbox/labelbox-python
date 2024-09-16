import json

from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.mixins import CustomMetric
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import (
    Label,
    ObjectAnnotation,
    Rectangle,
    Point,
    ClassificationAnnotation,
    Radio,
    ClassificationAnswer,
    Text,
    Checklist,
)


def test_nested():
    with open("tests/data/assets/ndjson/nested_import.json", "r") as file:
        data = json.load(file)
    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrb1sf1i1g7i0ybcdc6oc8ct",
            ),
            annotations=[
                ObjectAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={
                        "uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673",
                    },
                    value=Rectangle(
                        start=Point(x=2275.0, y=1352.0),
                        end=Point(x=2414.0, y=1702.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                            value=Radio(
                                answer=ClassificationAnswer(
                                    custom_metrics=[
                                        CustomMetric(
                                            name="customMetric1", value=0.5
                                        ),
                                        CustomMetric(
                                            name="customMetric2", value=0.3
                                        ),
                                    ],
                                    confidence=0.34,
                                    feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                                ),
                            ),
                        )
                    ],
                ),
                ObjectAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={
                        "uuid": "d009925d-91a3-4f67-abd9-753453f5a584",
                    },
                    value=Rectangle(
                        start=Point(x=2089.0, y=1251.0),
                        end=Point(x=2247.0, y=1679.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                            value=Radio(
                                answer=ClassificationAnswer(
                                    feature_schema_id="ckrb1sfl8099e0y919v260awv",
                                ),
                            ),
                        )
                    ],
                ),
                ObjectAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={
                        "uuid": "5d03213e-4408-456c-9eca-cf0723202961",
                    },
                    value=Rectangle(
                        start=Point(x=2089.0, y=1251.0),
                        end=Point(x=2247.0, y=1679.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                            value=Checklist(
                                answer=[
                                    ClassificationAnswer(
                                        custom_metrics=[
                                            CustomMetric(
                                                name="customMetric1", value=0.5
                                            ),
                                            CustomMetric(
                                                name="customMetric2", value=0.3
                                            ),
                                        ],
                                        confidence=0.894,
                                        feature_schema_id="ckrb1sfl8099e0y919v260awv",
                                    )
                                ],
                            ),
                        )
                    ],
                ),
                ObjectAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={
                        "uuid": "d50812f6-34eb-4f12-b3cb-bbde51a31d83",
                    },
                    value=Rectangle(
                        start=Point(x=2089.0, y=1251.0),
                        end=Point(x=2247.0, y=1679.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                            extra={},
                            value=Text(
                                answer="a string",
                            ),
                        )
                    ],
                ),
            ],
        )
    ]
    res = list(NDJsonConverter.serialize(labels))
    assert res == data


def test_nested_name_only():
    with open(
        "tests/data/assets/ndjson/nested_import_name_only.json", "r"
    ) as file:
        data = json.load(file)
    labels = [
        Label(
            data=GenericDataRowData(
                uid="ckrb1sf1i1g7i0ybcdc6oc8ct",
            ),
            annotations=[
                ObjectAnnotation(
                    name="box a",
                    extra={
                        "uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673",
                    },
                    value=Rectangle(
                        start=Point(x=2275.0, y=1352.0),
                        end=Point(x=2414.0, y=1702.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            name="classification a",
                            value=Radio(
                                answer=ClassificationAnswer(
                                    custom_metrics=[
                                        CustomMetric(
                                            name="customMetric1", value=0.5
                                        ),
                                        CustomMetric(
                                            name="customMetric2", value=0.3
                                        ),
                                    ],
                                    confidence=0.811,
                                    name="first answer",
                                ),
                            ),
                        )
                    ],
                ),
                ObjectAnnotation(
                    name="box b",
                    extra={
                        "uuid": "d009925d-91a3-4f67-abd9-753453f5a584",
                    },
                    value=Rectangle(
                        start=Point(x=2089.0, y=1251.0),
                        end=Point(x=2247.0, y=1679.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            name="classification b",
                            value=Radio(
                                answer=ClassificationAnswer(
                                    custom_metrics=[
                                        CustomMetric(
                                            name="customMetric1", value=0.5
                                        ),
                                        CustomMetric(
                                            name="customMetric2", value=0.3
                                        ),
                                    ],
                                    confidence=0.815,
                                    name="second answer",
                                ),
                            ),
                        )
                    ],
                ),
                ObjectAnnotation(
                    name="box c",
                    extra={
                        "uuid": "8a2b2c43-f0a1-4763-ba96-e322d986ced6",
                    },
                    value=Rectangle(
                        start=Point(x=2089.0, y=1251.0),
                        end=Point(x=2247.0, y=1679.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            name="classification c",
                            value=Checklist(
                                answer=[
                                    ClassificationAnswer(
                                        name="third answer",
                                    )
                                ],
                            ),
                        )
                    ],
                ),
                ObjectAnnotation(
                    name="box c",
                    extra={
                        "uuid": "456dd2c6-9fa0-42f9-9809-acc27b9886a7",
                    },
                    value=Rectangle(
                        start=Point(x=2089.0, y=1251.0),
                        end=Point(x=2247.0, y=1679.0),
                    ),
                    classifications=[
                        ClassificationAnnotation(
                            name="a string",
                            value=Text(
                                answer="a string",
                            ),
                        )
                    ],
                ),
            ],
        )
    ]
    res = list(NDJsonConverter.serialize(labels))
    assert res == data
