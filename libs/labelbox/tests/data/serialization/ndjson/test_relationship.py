import json

from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)

from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import (
    Label,
    ObjectAnnotation,
    Point,
    Rectangle,
    RelationshipAnnotation,
    Relationship,
)


def test_relationship():
    with open("tests/data/assets/ndjson/relationship_import.json", "r") as file:
        data = json.load(file)

    res = [
        Label(
            data=GenericDataRowData(
                uid="clf98gj90000qp38ka34yhptl",
            ),
            annotations=[
                ObjectAnnotation(
                    name="cat",
                    extra={
                        "uuid": "d8813907-b15d-4374-bbe6-b9877fb42ccd",
                    },
                    value=Rectangle(
                        start=Point(x=100.0, y=200.0),
                        end=Point(x=200.0, y=300.0),
                    ),
                ),
                ObjectAnnotation(
                    name="dog",
                    extra={
                        "uuid": "9b1e1249-36b4-4665-b60a-9060e0d18660",
                    },
                    value=Rectangle(
                        start=Point(x=400.0, y=500.0),
                        end=Point(x=600.0, y=700.0),
                    ),
                ),
                RelationshipAnnotation(
                    name="is chasing",
                    extra={"uuid": "0e6354eb-9adb-47e5-8e52-217ed016d948"},
                    value=Relationship(
                        source=ObjectAnnotation(
                            name="dog",
                            extra={
                                "uuid": "9b1e1249-36b4-4665-b60a-9060e0d18660",
                            },
                            value=Rectangle(
                                start=Point(x=400.0, y=500.0),
                                end=Point(x=600.0, y=700.0),
                            ),
                        ),
                        target=ObjectAnnotation(
                            name="cat",
                            extra={
                                "uuid": "d8813907-b15d-4374-bbe6-b9877fb42ccd",
                            },
                            value=Rectangle(
                                extra={},
                                start=Point(x=100.0, y=200.0),
                                end=Point(x=200.0, y=300.0),
                            ),
                        ),
                        type=Relationship.Type.UNIDIRECTIONAL,
                    ),
                ),
            ],
        ),
        Label(
            data=GenericDataRowData(
                uid="clf98gj90000qp38ka34yhptl-DIFFERENT",
            ),
            annotations=[
                ObjectAnnotation(
                    name="cat",
                    extra={
                        "uuid": "d8813907-b15d-4374-bbe6-b9877fb42ccd",
                    },
                    value=Rectangle(
                        start=Point(x=100.0, y=200.0),
                        end=Point(x=200.0, y=300.0),
                    ),
                ),
                ObjectAnnotation(
                    name="dog",
                    extra={
                        "uuid": "9b1e1249-36b4-4665-b60a-9060e0d18660",
                    },
                    value=Rectangle(
                        start=Point(x=400.0, y=500.0),
                        end=Point(x=600.0, y=700.0),
                    ),
                ),
                RelationshipAnnotation(
                    name="is chasing",
                    extra={"uuid": "0e6354eb-9adb-47e5-8e52-217ed016d948"},
                    value=Relationship(
                        source=ObjectAnnotation(
                            name="dog",
                            extra={
                                "uuid": "9b1e1249-36b4-4665-b60a-9060e0d18660",
                            },
                            value=Rectangle(
                                start=Point(x=400.0, y=500.0),
                                end=Point(x=600.0, y=700.0),
                            ),
                        ),
                        target=ObjectAnnotation(
                            name="cat",
                            extra={
                                "uuid": "d8813907-b15d-4374-bbe6-b9877fb42ccd",
                            },
                            value=Rectangle(
                                start=Point(x=100.0, y=200.0),
                                end=Point(x=200.0, y=300.0),
                            ),
                        ),
                        type=Relationship.Type.UNIDIRECTIONAL,
                    ),
                ),
            ],
        ),
    ]
    res = list(NDJsonConverter.serialize(res))
    assert len(res) == len(data)

    res_relationship_annotation, res_relationship_second_annotation = [
        annot for annot in res if "relationship" in annot
    ]
    res_source_and_target = [
        annot for annot in res if "relationship" not in annot
    ]
    assert res_relationship_annotation

    assert res_relationship_annotation["relationship"]["source"] in [
        annot["uuid"] for annot in res_source_and_target
    ]
    assert res_relationship_annotation["relationship"]["target"] in [
        annot["uuid"] for annot in res_source_and_target
    ]

    assert res_relationship_second_annotation
    assert (
        res_relationship_second_annotation["relationship"]["source"]
        != res_relationship_annotation["relationship"]["source"]
    )
    assert (
        res_relationship_second_annotation["relationship"]["target"]
        != res_relationship_annotation["relationship"]["target"]
    )
    assert res_relationship_second_annotation["relationship"]["source"] in [
        annot["uuid"] for annot in res_source_and_target
    ]
    assert res_relationship_second_annotation["relationship"]["target"] in [
        annot["uuid"] for annot in res_source_and_target
    ]
