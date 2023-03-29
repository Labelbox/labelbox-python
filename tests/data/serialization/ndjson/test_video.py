import json
from labelbox.data.annotation_types.classification.classification import Checklist, ClassificationAnnotation, ClassificationAnswer, Radio
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.video import VideoClassificationAnnotation

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_video():
    with open('tests/data/assets/ndjson/video_import.json', 'r') as file:
        data = json.load(file)

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == [data[2], data[0], data[1], data[3], data[4], data[5]]


def test_video_name_only():
    with open('tests/data/assets/ndjson/video_import_name_only.json',
              'r') as file:
        data = json.load(file)

    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == [data[2], data[0], data[1], data[3], data[4], data[5]]


def test_video_classification_global_subclassifications():
    label = Label(
        data=VideoData(global_key="sample-video-4.mp4",),
        annotations=[
            ClassificationAnnotation(
                name='radio_question_nested',
                value=Radio(answer=ClassificationAnswer(
                    name='first_radio_question')),
            ),
            ClassificationAnnotation(
                name='nested_checklist_question',
                value=Checklist(
                    name='checklist',
                    answer=[
                        ClassificationAnswer(
                            name='first_checklist_answer',
                            classifications=[
                                ClassificationAnnotation(
                                    name='sub_checklist_question',
                                    value=Radio(answer=ClassificationAnswer(
                                        name='first_sub_checklist_answer')))
                            ])
                    ]))
        ])

    expected_first_annotation = {
        'name': 'radio_question_nested',
        'answer': {
            'name': 'first_radio_question'
        },
        'dataRow': {
            'globalKey': 'sample-video-4.mp4'
        }
    }

    expected_second_annotation = nested_checklist_annotation_ndjson = {
        "name": "nested_checklist_question",
        "answer": [{
            "name":
                "first_checklist_answer",
            "classifications": [{
                "name": "sub_checklist_question",
                "answer": {
                    "name": "first_sub_checklist_answer"
                }
            }]
        }],
        'dataRow': {
            'globalKey': 'sample-video-4.mp4'
        }
    }

    serialized = NDJsonConverter.serialize([label])
    res = [x for x in serialized]
    for annotations in res:
        annotations.pop("uuid")
    assert res == [expected_first_annotation, expected_second_annotation]

    deserialized = NDJsonConverter.deserialize(res)
    res = next(deserialized)
    annotations = res.annotations
    for annotation in annotations:
        annotation.extra.pop("uuid")
    assert annotations == label.annotations
