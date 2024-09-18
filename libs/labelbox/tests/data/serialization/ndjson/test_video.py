import json
from operator import itemgetter

from labelbox.data.annotation_types.classification.classification import (
    Checklist,
    ClassificationAnnotation,
    ClassificationAnswer,
    Radio,
)
from labelbox.data.annotation_types.data import GenericDataRowData
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.video import (
    VideoClassificationAnnotation,
    VideoObjectAnnotation,
)
from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_video():
    with open("tests/data/assets/ndjson/video_import.json", "r") as file:
        data = json.load(file)

    labels = [
        Label(
            data=GenericDataRowData(uid="ckrb1sf1i1g7i0ybcdc6oc8ct"),
            annotations=[
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=30,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=31,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=32,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=33,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=34,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=35,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=50,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfjx099a0y914hl319ie",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            feature_schema_id="ckrb1sfl8099g0y91cxbd5ftb",
                        ),
                    ),
                    frame=51,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                feature_schema_id="ckrb1sfl8099e0y919v260awv",
                            )
                        ],
                    ),
                    frame=0,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                feature_schema_id="ckrb1sfl8099e0y919v260awv",
                            )
                        ],
                    ),
                    frame=1,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                feature_schema_id="ckrb1sfl8099e0y919v260awv",
                            )
                        ],
                    ),
                    frame=2,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                feature_schema_id="ckrb1sfl8099e0y919v260awv",
                            )
                        ],
                    ),
                    frame=3,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                feature_schema_id="ckrb1sfl8099e0y919v260awv",
                            )
                        ],
                    ),
                    frame=4,
                ),
                VideoClassificationAnnotation(
                    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                feature_schema_id="ckrb1sfl8099e0y919v260awv",
                            )
                        ],
                    ),
                    frame=5,
                ),
                ClassificationAnnotation(
                    feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
                    extra={"uuid": "90e2ecf7-c19c-47e6-8cdb-8867e1b9d88c"},
                    value=Text(answer="a value"),
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5islwg200gfci6g0oitaypu",
                    extra={"uuid": "6f7c835a-0139-4896-b73f-66a6baa89e94"},
                    value=Line(
                        points=[
                            Point(x=10.0, y=10.0),
                            Point(x=100.0, y=100.0),
                            Point(x=50.0, y=30.0),
                        ],
                    ),
                    frame=1,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5islwg200gfci6g0oitaypu",
                    extra={"uuid": "6f7c835a-0139-4896-b73f-66a6baa89e94"},
                    value=Line(
                        points=[
                            Point(x=15.0, y=10.0),
                            Point(x=50.0, y=100.0),
                            Point(x=50.0, y=30.0),
                        ],
                    ),
                    frame=5,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5islwg200gfci6g0oitaypu",
                    extra={"uuid": "6f7c835a-0139-4896-b73f-66a6baa89e94"},
                    value=Line(
                        points=[
                            Point(x=100.0, y=10.0),
                            Point(x=50.0, y=100.0),
                            Point(x=50.0, y=30.0),
                        ],
                    ),
                    frame=8,
                    keyframe=True,
                    segment_index=1,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5it7ktp00i5ci6gf80b1ysd",
                    extra={"uuid": "f963be22-227b-4efe-9be4-2738ed822216"},
                    value=Point(x=10.0, y=10.0),
                    frame=1,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5it7ktp00i5ci6gf80b1ysd",
                    extra={"uuid": "f963be22-227b-4efe-9be4-2738ed822216"},
                    value=Point(x=50.0, y=50.0),
                    frame=5,
                    keyframe=True,
                    segment_index=1,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5it7ktp00i5ci6gf80b1ysd",
                    extra={"uuid": "f963be22-227b-4efe-9be4-2738ed822216"},
                    value=Point(x=10.0, y=50.0),
                    frame=10,
                    keyframe=True,
                    segment_index=1,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5iw0roz00lwci6g5jni62vs",
                    extra={"uuid": "13b2ee0e-2355-4336-8b83-d74d09e3b1e7"},
                    value=Rectangle(
                        start=Point(x=5.0, y=10.0),
                        end=Point(x=155.0, y=110.0),
                    ),
                    frame=1,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5iw0roz00lwci6g5jni62vs",
                    extra={"uuid": "13b2ee0e-2355-4336-8b83-d74d09e3b1e7"},
                    value=Rectangle(
                        start=Point(x=5.0, y=30.0),
                        end=Point(x=155.0, y=80.0),
                    ),
                    frame=5,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    feature_schema_id="cl5iw0roz00lwci6g5jni62vs",
                    extra={"uuid": "13b2ee0e-2355-4336-8b83-d74d09e3b1e7"},
                    value=Rectangle(
                        start=Point(x=200.0, y=300.0),
                        end=Point(x=350.0, y=700.0),
                    ),
                    frame=10,
                    keyframe=True,
                    segment_index=1,
                ),
            ],
        )
    ]

    res = list(NDJsonConverter.serialize(labels))

    data = sorted(data, key=itemgetter("uuid"))
    res = sorted(res, key=itemgetter("uuid"))

    pairs = zip(data, res)
    for data, res in pairs:
        assert data == res


def test_video_name_only():
    with open(
        "tests/data/assets/ndjson/video_import_name_only.json", "r"
    ) as file:
        data = json.load(file)
    labels = [
        Label(
            data=GenericDataRowData(uid="ckrb1sf1i1g7i0ybcdc6oc8ct"),
            annotations=[
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=30,
                ),
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=31,
                ),
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=32,
                ),
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=33,
                ),
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=34,
                ),
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=35,
                ),
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=50,
                ),
                VideoClassificationAnnotation(
                    name="question 1",
                    extra={"uuid": "f6879f59-d2b5-49c2-aceb-d9e8dc478673"},
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="answer 1",
                        ),
                    ),
                    frame=51,
                ),
                VideoClassificationAnnotation(
                    name="question 2",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="answer 2",
                            )
                        ],
                    ),
                    frame=0,
                ),
                VideoClassificationAnnotation(
                    name="question 2",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="answer 2",
                            )
                        ],
                    ),
                    frame=1,
                ),
                VideoClassificationAnnotation(
                    name="question 2",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="answer 2",
                            )
                        ],
                    ),
                    frame=2,
                ),
                VideoClassificationAnnotation(
                    name="question 2",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="answer 2",
                            )
                        ],
                    ),
                    frame=3,
                ),
                VideoClassificationAnnotation(
                    name="question 2",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="answer 2",
                            )
                        ],
                    ),
                    frame=4,
                ),
                VideoClassificationAnnotation(
                    name="question 2",
                    extra={"uuid": "d009925d-91a3-4f67-abd9-753453f5a584"},
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="answer 2",
                            )
                        ],
                    ),
                    frame=5,
                ),
                ClassificationAnnotation(
                    name="question 3",
                    extra={"uuid": "e5f32456-bd67-4520-8d3b-cbeb2204bad3"},
                    value=Text(answer="a value"),
                ),
                VideoObjectAnnotation(
                    name="segment 1",
                    extra={"uuid": "6f7c835a-0139-4896-b73f-66a6baa89e94"},
                    value=Line(
                        points=[
                            Point(x=10.0, y=10.0),
                            Point(x=100.0, y=100.0),
                            Point(x=50.0, y=30.0),
                        ],
                    ),
                    frame=1,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    name="segment 1",
                    extra={"uuid": "6f7c835a-0139-4896-b73f-66a6baa89e94"},
                    value=Line(
                        points=[
                            Point(x=15.0, y=10.0),
                            Point(x=50.0, y=100.0),
                            Point(x=50.0, y=30.0),
                        ],
                    ),
                    frame=5,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    name="segment 1",
                    extra={"uuid": "6f7c835a-0139-4896-b73f-66a6baa89e94"},
                    value=Line(
                        points=[
                            Point(x=100.0, y=10.0),
                            Point(x=50.0, y=100.0),
                            Point(x=50.0, y=30.0),
                        ],
                    ),
                    frame=8,
                    keyframe=True,
                    segment_index=1,
                ),
                VideoObjectAnnotation(
                    name="segment 2",
                    extra={"uuid": "f963be22-227b-4efe-9be4-2738ed822216"},
                    value=Point(x=10.0, y=10.0),
                    frame=1,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    name="segment 2",
                    extra={"uuid": "f963be22-227b-4efe-9be4-2738ed822216"},
                    value=Point(x=50.0, y=50.0),
                    frame=5,
                    keyframe=True,
                    segment_index=1,
                ),
                VideoObjectAnnotation(
                    name="segment 2",
                    extra={"uuid": "f963be22-227b-4efe-9be4-2738ed822216"},
                    value=Point(x=10.0, y=50.0),
                    frame=10,
                    keyframe=True,
                    segment_index=1,
                ),
                VideoObjectAnnotation(
                    name="segment 3",
                    extra={"uuid": "13b2ee0e-2355-4336-8b83-d74d09e3b1e7"},
                    value=Rectangle(
                        start=Point(x=5.0, y=10.0),
                        end=Point(x=155.0, y=110.0),
                    ),
                    frame=1,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    name="segment 3",
                    extra={"uuid": "13b2ee0e-2355-4336-8b83-d74d09e3b1e7"},
                    value=Rectangle(
                        start=Point(x=5.0, y=30.0),
                        end=Point(x=155.0, y=80.0),
                    ),
                    frame=5,
                    keyframe=True,
                    segment_index=0,
                ),
                VideoObjectAnnotation(
                    name="segment 3",
                    extra={"uuid": "13b2ee0e-2355-4336-8b83-d74d09e3b1e7"},
                    value=Rectangle(
                        start=Point(x=200.0, y=300.0),
                        end=Point(x=350.0, y=700.0),
                    ),
                    frame=10,
                    keyframe=True,
                    segment_index=1,
                ),
            ],
        )
    ]
    res = list(NDJsonConverter.serialize(labels))
    data = sorted(data, key=itemgetter("uuid"))
    res = sorted(res, key=itemgetter("uuid"))

    pairs = zip(data, res)
    for data, res in pairs:
        assert data == res


def test_video_classification_global_subclassifications():
    label = Label(
        data=GenericDataRowData(
            global_key="sample-video-4.mp4",
        ),
        annotations=[
            ClassificationAnnotation(
                name="radio_question_nested",
                value=Radio(
                    answer=ClassificationAnswer(name="first_radio_question")
                ),
            ),
            ClassificationAnnotation(
                name="nested_checklist_question",
                value=Checklist(
                    name="checklist",
                    answer=[
                        ClassificationAnswer(
                            name="first_checklist_answer",
                            classifications=[
                                ClassificationAnnotation(
                                    name="sub_checklist_question",
                                    value=Radio(
                                        answer=ClassificationAnswer(
                                            name="first_sub_checklist_answer"
                                        )
                                    ),
                                )
                            ],
                        )
                    ],
                ),
            ),
        ],
    )

    expected_first_annotation = {
        "name": "radio_question_nested",
        "answer": {"name": "first_radio_question"},
        "dataRow": {"globalKey": "sample-video-4.mp4"},
    }

    expected_second_annotation = nested_checklist_annotation_ndjson = {
        "name": "nested_checklist_question",
        "answer": [
            {
                "name": "first_checklist_answer",
                "classifications": [
                    {
                        "name": "sub_checklist_question",
                        "answer": {"name": "first_sub_checklist_answer"},
                    }
                ],
            }
        ],
        "dataRow": {"globalKey": "sample-video-4.mp4"},
    }

    serialized = NDJsonConverter.serialize([label])
    res = [x for x in serialized]
    for annotations in res:
        annotations.pop("uuid")
    assert res == [expected_first_annotation, expected_second_annotation]

    deserialized = NDJsonConverter.deserialize(res)
    res = next(deserialized)
    annotations = res.annotations
    for i, annotation in enumerate(annotations):
        assert annotation.name == label.annotations[i].name


def test_video_classification_nesting_bbox():
    bbox_annotation = [
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=13,
            segment_index=0,
            value=Rectangle(
                start=Point(x=146.0, y=98.0),  # Top left
                end=Point(x=382.0, y=341.0),  # Bottom right
            ),
            classifications=[
                ClassificationAnnotation(
                    name="radio_question_nested",
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="first_radio_question",
                            classifications=[
                                ClassificationAnnotation(
                                    name="sub_question_radio",
                                    value=Checklist(
                                        answer=[
                                            ClassificationAnswer(
                                                name="sub_answer"
                                            )
                                        ]
                                    ),
                                )
                            ],
                        )
                    ),
                )
            ],
        ),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=15,
            segment_index=0,
            value=Rectangle(
                start=Point(x=146.0, y=98.0),  # Top left
                end=Point(x=382.0, y=341.0),  # Bottom right,
            ),
            classifications=[
                ClassificationAnnotation(
                    name="nested_checklist_question",
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="first_checklist_answer",
                                classifications=[
                                    ClassificationAnnotation(
                                        name="sub_checklist_question",
                                        value=Radio(
                                            answer=ClassificationAnswer(
                                                name="first_sub_checklist_answer"
                                            )
                                        ),
                                    )
                                ],
                            )
                        ]
                    ),
                )
            ],
        ),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=19,
            segment_index=0,
            value=Rectangle(
                start=Point(x=146.0, y=98.0),  # Top left
                end=Point(x=382.0, y=341.0),  # Bottom right
            ),
        ),
    ]
    expected = [
        {
            "dataRow": {"globalKey": "sample-video-4.mp4"},
            "name": "bbox_video",
            "classifications": [],
            "segments": [
                {
                    "keyframes": [
                        {
                            "frame": 13,
                            "bbox": {
                                "top": 98.0,
                                "left": 146.0,
                                "height": 243.0,
                                "width": 236.0,
                            },
                            "classifications": [
                                {
                                    "name": "radio_question_nested",
                                    "answer": {
                                        "name": "first_radio_question",
                                        "classifications": [
                                            {
                                                "name": "sub_question_radio",
                                                "answer": [
                                                    {"name": "sub_answer"}
                                                ],
                                            }
                                        ],
                                    },
                                }
                            ],
                        },
                        {
                            "frame": 15,
                            "bbox": {
                                "top": 98.0,
                                "left": 146.0,
                                "height": 243.0,
                                "width": 236.0,
                            },
                            "classifications": [
                                {
                                    "name": "nested_checklist_question",
                                    "answer": [
                                        {
                                            "name": "first_checklist_answer",
                                            "classifications": [
                                                {
                                                    "name": "sub_checklist_question",
                                                    "answer": {
                                                        "name": "first_sub_checklist_answer"
                                                    },
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "frame": 19,
                            "bbox": {
                                "top": 98.0,
                                "left": 146.0,
                                "height": 243.0,
                                "width": 236.0,
                            },
                            "classifications": [],
                        },
                    ]
                }
            ],
        }
    ]

    label = Label(
        data=GenericDataRowData(
            global_key="sample-video-4.mp4",
        ),
        annotations=bbox_annotation,
    )

    serialized = NDJsonConverter.serialize([label])
    res = [x for x in serialized]
    assert res == expected

    deserialized = NDJsonConverter.deserialize(res)
    res = next(deserialized)
    annotations = res.annotations
    for i, annotation in enumerate(annotations):
        annotation.extra.pop("uuid")
        assert annotation.value == label.annotations[i].value
        assert annotation.name == label.annotations[i].name


def test_video_classification_point():
    bbox_annotation = [
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=13,
            segment_index=0,
            value=Point(x=46.0, y=8.0),
            classifications=[
                ClassificationAnnotation(
                    name="radio_question_nested",
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="first_radio_question",
                            classifications=[
                                ClassificationAnnotation(
                                    name="sub_question_radio",
                                    value=Checklist(
                                        answer=[
                                            ClassificationAnswer(
                                                name="sub_answer"
                                            )
                                        ]
                                    ),
                                )
                            ],
                        )
                    ),
                )
            ],
        ),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=15,
            segment_index=0,
            value=Point(x=56.0, y=18.0),
            classifications=[
                ClassificationAnnotation(
                    name="nested_checklist_question",
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="first_checklist_answer",
                                classifications=[
                                    ClassificationAnnotation(
                                        name="sub_checklist_question",
                                        value=Radio(
                                            answer=ClassificationAnswer(
                                                name="first_sub_checklist_answer"
                                            )
                                        ),
                                    )
                                ],
                            )
                        ]
                    ),
                )
            ],
        ),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=19,
            segment_index=0,
            value=Point(x=66.0, y=28.0),
        ),
    ]
    expected = [
        {
            "dataRow": {"globalKey": "sample-video-4.mp4"},
            "name": "bbox_video",
            "classifications": [],
            "segments": [
                {
                    "keyframes": [
                        {
                            "frame": 13,
                            "point": {
                                "x": 46.0,
                                "y": 8.0,
                            },
                            "classifications": [
                                {
                                    "name": "radio_question_nested",
                                    "answer": {
                                        "name": "first_radio_question",
                                        "classifications": [
                                            {
                                                "name": "sub_question_radio",
                                                "answer": [
                                                    {"name": "sub_answer"}
                                                ],
                                            }
                                        ],
                                    },
                                }
                            ],
                        },
                        {
                            "frame": 15,
                            "point": {
                                "x": 56.0,
                                "y": 18.0,
                            },
                            "classifications": [
                                {
                                    "name": "nested_checklist_question",
                                    "answer": [
                                        {
                                            "name": "first_checklist_answer",
                                            "classifications": [
                                                {
                                                    "name": "sub_checklist_question",
                                                    "answer": {
                                                        "name": "first_sub_checklist_answer"
                                                    },
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "frame": 19,
                            "point": {
                                "x": 66.0,
                                "y": 28.0,
                            },
                            "classifications": [],
                        },
                    ]
                }
            ],
        }
    ]

    label = Label(
        data=GenericDataRowData(
            global_key="sample-video-4.mp4",
        ),
        annotations=bbox_annotation,
    )

    serialized = NDJsonConverter.serialize([label])
    res = [x for x in serialized]
    assert res == expected

    deserialized = NDJsonConverter.deserialize(res)
    res = next(deserialized)
    annotations = res.annotations
    for i, annotation in enumerate(annotations):
        annotation.extra.pop("uuid")
        assert annotation.value == label.annotations[i].value


def test_video_classification_frameline():
    bbox_annotation = [
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=13,
            segment_index=0,
            value=Line(points=[Point(x=8, y=10), Point(x=10, y=9)]),
            classifications=[
                ClassificationAnnotation(
                    name="radio_question_nested",
                    value=Radio(
                        answer=ClassificationAnswer(
                            name="first_radio_question",
                            classifications=[
                                ClassificationAnnotation(
                                    name="sub_question_radio",
                                    value=Checklist(
                                        answer=[
                                            ClassificationAnswer(
                                                name="sub_answer"
                                            )
                                        ]
                                    ),
                                )
                            ],
                        )
                    ),
                )
            ],
        ),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=15,
            segment_index=0,
            value=Line(points=[Point(x=18, y=20), Point(x=20, y=19)]),
            classifications=[
                ClassificationAnnotation(
                    name="nested_checklist_question",
                    value=Checklist(
                        answer=[
                            ClassificationAnswer(
                                name="first_checklist_answer",
                                classifications=[
                                    ClassificationAnnotation(
                                        name="sub_checklist_question",
                                        value=Radio(
                                            answer=ClassificationAnswer(
                                                name="first_sub_checklist_answer"
                                            )
                                        ),
                                    )
                                ],
                            )
                        ]
                    ),
                )
            ],
        ),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=19,
            segment_index=0,
            value=Line(points=[Point(x=28, y=30), Point(x=30, y=29)]),
        ),
    ]
    expected = [
        {
            "dataRow": {"globalKey": "sample-video-4.mp4"},
            "name": "bbox_video",
            "classifications": [],
            "segments": [
                {
                    "keyframes": [
                        {
                            "frame": 13,
                            "line": [
                                {
                                    "x": 8.0,
                                    "y": 10.0,
                                },
                                {
                                    "x": 10.0,
                                    "y": 9.0,
                                },
                            ],
                            "classifications": [
                                {
                                    "name": "radio_question_nested",
                                    "answer": {
                                        "name": "first_radio_question",
                                        "classifications": [
                                            {
                                                "name": "sub_question_radio",
                                                "answer": [
                                                    {"name": "sub_answer"}
                                                ],
                                            }
                                        ],
                                    },
                                }
                            ],
                        },
                        {
                            "frame": 15,
                            "line": [
                                {
                                    "x": 18.0,
                                    "y": 20.0,
                                },
                                {
                                    "x": 20.0,
                                    "y": 19.0,
                                },
                            ],
                            "classifications": [
                                {
                                    "name": "nested_checklist_question",
                                    "answer": [
                                        {
                                            "name": "first_checklist_answer",
                                            "classifications": [
                                                {
                                                    "name": "sub_checklist_question",
                                                    "answer": {
                                                        "name": "first_sub_checklist_answer"
                                                    },
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "frame": 19,
                            "line": [
                                {
                                    "x": 28.0,
                                    "y": 30.0,
                                },
                                {
                                    "x": 30.0,
                                    "y": 29.0,
                                },
                            ],
                            "classifications": [],
                        },
                    ]
                }
            ],
        }
    ]

    label = Label(
        data=GenericDataRowData(
            global_key="sample-video-4.mp4",
        ),
        annotations=bbox_annotation,
    )
    serialized = NDJsonConverter.serialize([label])
    res = [x for x in serialized]
    assert res == expected

    deserialized = NDJsonConverter.deserialize(res)
    res = next(deserialized)
    annotations = res.annotations
    for i, annotation in enumerate(annotations):
        annotation.extra.pop("uuid")
        assert annotation.value == label.annotations[i].value
