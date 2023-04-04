import json
from labelbox.client import Client
from labelbox.data.annotation_types.classification.classification import Checklist, ClassificationAnnotation, ClassificationAnswer, Radio
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.geometry.point import Point

from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.video import VideoObjectAnnotation
import ndjson

from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.schema.annotation_import import MALPredictionImport


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
                    name='radio_question_nested',
                    value=Radio(answer=ClassificationAnswer(
                        name='first_radio_question',
                        classifications=[
                            ClassificationAnnotation(name='sub_question_radio',
                                                     value=Checklist(answer=[
                                                         ClassificationAnswer(
                                                             name='sub_answer')
                                                     ]))
                        ])),
                )
            ]),
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
                    name='nested_checklist_question',
                    value=Checklist(answer=[
                        ClassificationAnswer(
                            name='first_checklist_answer',
                            classifications=[
                                ClassificationAnnotation(
                                    name='sub_checklist_question',
                                    value=Radio(answer=ClassificationAnswer(
                                        name='first_sub_checklist_answer')))
                            ])
                    ]))
            ]),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=19,
            segment_index=0,
            value=Rectangle(
                start=Point(x=146.0, y=98.0),  # Top left
                end=Point(x=382.0, y=341.0),  # Bottom right
            ))
    ]
    expected = [{
        'dataRow': {
            'globalKey': 'sample-video-4.mp4'
        },
        'name':
            'bbox_video',
        'classifications': [],
        'segments': [{
            'keyframes': [{
                'frame':
                    13,
                'bbox': {
                    'top': 98.0,
                    'left': 146.0,
                    'height': 243.0,
                    'width': 236.0
                },
                'classifications': [{
                    'name': 'radio_question_nested',
                    'answer': {
                        'name':
                            'first_radio_question',
                        'classifications': [{
                            'name': 'sub_question_radio',
                            'answer': [{
                                'name': 'sub_answer'
                            }]
                        }]
                    }
                }]
            }, {
                'frame':
                    15,
                'bbox': {
                    'top': 98.0,
                    'left': 146.0,
                    'height': 243.0,
                    'width': 236.0
                },
                'classifications': [{
                    'name':
                        'nested_checklist_question',
                    'answer': [{
                        'name':
                            'first_checklist_answer',
                        'classifications': [{
                            'name': 'sub_checklist_question',
                            'answer': {
                                'name': 'first_sub_checklist_answer'
                            }
                        }]
                    }]
                }]
            }, {
                'frame': 19,
                'bbox': {
                    'top': 98.0,
                    'left': 146.0,
                    'height': 243.0,
                    'width': 236.0
                },
                'classifications': []
            }]
        }]
    }]

    label = Label(data=VideoData(global_key="sample-video-4.mp4",),
                  annotations=bbox_annotation)

    serialized = NDJsonConverter.serialize([label])
    res = [x for x in serialized]
    for annotations in res:
        annotations.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize(res)
    res = next(deserialized)
    annotations = res.annotations
    for annotation in annotations:
        annotation.extra.pop("uuid")
    assert annotations == label.annotations


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
                    name='radio_question_nested',
                    value=Radio(answer=ClassificationAnswer(
                        name='first_radio_question',
                        classifications=[
                            ClassificationAnnotation(name='sub_question_radio',
                                                     value=Checklist(answer=[
                                                         ClassificationAnswer(
                                                             name='sub_answer')
                                                     ]))
                        ])),
                )
            ]),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=15,
            segment_index=0,
            value=Point(x=56.0, y=18.0),
            classifications=[
                ClassificationAnnotation(
                    name='nested_checklist_question',
                    value=Checklist(answer=[
                        ClassificationAnswer(
                            name='first_checklist_answer',
                            classifications=[
                                ClassificationAnnotation(
                                    name='sub_checklist_question',
                                    value=Radio(answer=ClassificationAnswer(
                                        name='first_sub_checklist_answer')))
                            ])
                    ]))
            ]),
        VideoObjectAnnotation(
            name="bbox_video",
            keyframe=True,
            frame=19,
            segment_index=0,
            value=Point(x=66.0, y=28.0),
        )
    ]
    expected = [{
        'dataRow': {
            'globalKey': 'sample-video-4.mp4'
        },
        'name':
            'bbox_video',
        'classifications': [],
        'segments': [{
            'keyframes': [{
                'frame':
                    13,
                'point': {
                    'x': 46.0,
                    'y': 8.0,
                },
                'classifications': [{
                    'name': 'radio_question_nested',
                    'answer': {
                        'name':
                            'first_radio_question',
                        'classifications': [{
                            'name': 'sub_question_radio',
                            'answer': [{
                                'name': 'sub_answer'
                            }]
                        }]
                    }
                }]
            }, {
                'frame':
                    15,
                'point': {
                    'x': 56.0,
                    'y': 18.0,
                },
                'classifications': [{
                    'name':
                        'nested_checklist_question',
                    'answer': [{
                        'name':
                            'first_checklist_answer',
                        'classifications': [{
                            'name': 'sub_checklist_question',
                            'answer': {
                                'name': 'first_sub_checklist_answer'
                            }
                        }]
                    }]
                }]
            }, {
                'frame': 19,
                'point': {
                    'x': 66.0,
                    'y': 28.0,
                },
                'classifications': []
            }]
        }]
    }]

    label = Label(data=VideoData(global_key="sample-video-4.mp4",),
                  annotations=bbox_annotation)

    serialized = NDJsonConverter.serialize([label])
    res = [x for x in serialized]
    for annotations in res:
        annotations.pop("uuid")
    assert res == expected

    deserialized = NDJsonConverter.deserialize(res)
    res = next(deserialized)
    annotations = res.annotations
    for annotation in annotations:
        annotation.extra.pop("uuid")
    assert annotations == label.annotations


# def test_deserialization_video_objects():

#     bbox_annotation_ndjson = [{
#         'name': 'bbox_video',
#         'segments': [{
#             'keyframes': [{
#                 'frame':
#                     13,
#                 'bbox': {
#                     'top': 146.0,
#                     'left': 98.0,
#                     'height': 382.0,
#                     'width': 341.0
#                 },
#                 'classifications': [{
#                     'name':
#                         'radio_question_nested',
#                     'answer': {
#                         'name': 'first_radio_question'
#                     },
#                     'classifications': [{
#                         'name': 'sub_question_radio',
#                         'answer': {
#                             'name': 'sub_answer'
#                         }
#                     }]
#                 }]
#             }, {
#                 'frame':
#                     15,
#                 'bbox': {
#                     'top': 146.0,
#                     'left': 98.0,
#                     'height': 382.0,
#                     'width': 341.0
#                 },
#                 'classifications': [{
#                     'name':
#                         'nested_checklist_question',
#                     'answer': [{
#                         'name':
#                             'first_checklist_answer',
#                         'classifications': [{
#                             'name': 'sub_checklist_question',
#                             'answer': {
#                                 'name': 'first_sub_checklist_answer'
#                             }
#                         }]
#                     }]
#                 }]
#             }, {
#                 'frame': 19,
#                 'bbox': {
#                     'top': 146.0,
#                     'left': 98.0,
#                     'height': 382.0,
#                     'width': 341.0
#                 }
#             }]
#         }],
#         'dataRow': {
#             'globalKey': 'sample-video-7.mp4'
#         }
#     }]

#     deserialized = NDJsonConverter.deserialize(bbox_annotation_ndjson)
#     res = next(deserialized)
#     import pdb
#     pdb.set_trace()
#     annotations = res.annotations
#     for annotation in annotations:
#         annotation.extra.pop("uuid")
#     assert annotations == label.annotations

#     # import pdb
#     # pdb.set_trace()
#     # api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbGRvczU1bnowMDBka3V1M2F1NDBobHR5Iiwib3JnYW5pemF0aW9uSWQiOiJjbGRvczU1bmwwMDBja3V1Mzc3eGM4YjY1IiwiYXBpS2V5SWQiOiJjbGZya2IxYTUwMHF6ZzUxNDFhejU5emR3Iiwic2VjcmV0IjoiZGQ4OTgxM2NiNzljOTU2NWQwYjYzMmRjMGI1ODdkNWEiLCJpYXQiOjE2Nzk5NjU4NzUsImV4cCI6MjMxMTExNzg3NX0._A46R_cp8bL3GWCso1_6qKlD45Q6NTIVF-ZWdEgGT9c"
#     # client = Client(api_key=api_key, endpoint="http://localhost:8080/graphql")
#     # upload_job_mal = MALPredictionImport.create_from_objects(
#     #     client=client,
#     #     project_id="clfvn5yuh00nn3pu39pd89wm6",
#     #     name="mal_import_job-23",
#     #     predictions=bbox_annotation_ndjson)
#     # upload_job_mal.wait_until_done()
#     # print("Errors:", upload_job_mal.errors)
