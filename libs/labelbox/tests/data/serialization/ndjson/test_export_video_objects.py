from labelbox.data.annotation_types import Label, VideoObjectAnnotation
from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.data.annotation_types.geometry import Rectangle, Point
from labelbox.data.annotation_types import VideoData


def video_bbox_label():
    return Label(
        uid='cl1z52xwh00050fhcmfgczqvn',
        data=VideoData(
            uid="cklr9mr4m5iao0rb6cvxu4qbn",
            file_path=None,
            frames=None,
            url=
            "https://storage.labelbox.com/ckcz6bubudyfi0855o1dt1g9s%2F26403a22-604a-a38c-eeff-c2ed481fb40a-cat.mp4?Expires=1651677421050&KeyName=labelbox-assets-key-3&Signature=vF7gMyfHzgZdfbB8BHgd88Ws-Ms"
        ),
        annotations=[
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=46.0),
                                                  end=Point(extra={},
                                                            x=454.0,
                                                            y=295.0)),
                                  classifications=[],
                                  frame=1,
                                  keyframe=True),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=42.5),
                                                  end=Point(extra={},
                                                            x=427.25,
                                                            y=308.25)),
                                  classifications=[],
                                  frame=2,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=39.0),
                                                  end=Point(extra={},
                                                            x=400.5,
                                                            y=321.5)),
                                  classifications=[],
                                  frame=3,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=35.5),
                                                  end=Point(extra={},
                                                            x=373.75,
                                                            y=334.75)),
                                  classifications=[],
                                  frame=4,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=32.0),
                                                  end=Point(extra={},
                                                            x=347.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=5,
                                  keyframe=True),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=132.0),
                                                  end=Point(extra={},
                                                            x=283.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=9,
                                  keyframe=True),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=122.333),
                                                  end=Point(extra={},
                                                            x=295.5,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=10,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=112.667),
                                                  end=Point(extra={},
                                                            x=308.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=11,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=103.0),
                                                  end=Point(extra={},
                                                            x=320.5,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=12,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=93.333),
                                                  end=Point(extra={},
                                                            x=333.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=13,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=83.667),
                                                  end=Point(extra={},
                                                            x=345.5,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=14,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=74.0),
                                                  end=Point(extra={},
                                                            x=358.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=15,
                                  keyframe=True),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=66.833),
                                                  end=Point(extra={},
                                                            x=387.333,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=16,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=59.667),
                                                  end=Point(extra={},
                                                            x=416.667,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=17,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=52.5),
                                                  end=Point(extra={},
                                                            x=446.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=18,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=45.333),
                                                  end=Point(extra={},
                                                            x=475.333,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=19,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=38.167),
                                                  end=Point(extra={},
                                                            x=504.667,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=20,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=31.0),
                                                  end=Point(extra={},
                                                            x=534.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=21,
                                  keyframe=True),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=29.5),
                                                  end=Point(extra={},
                                                            x=543.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=22,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=28.0),
                                                  end=Point(extra={},
                                                            x=552.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=23,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=26.5),
                                                  end=Point(extra={},
                                                            x=561.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=24,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=25.0),
                                                  end=Point(extra={},
                                                            x=570.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=25,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=23.5),
                                                  end=Point(extra={},
                                                            x=579.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=26,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=22.0),
                                                  end=Point(extra={},
                                                            x=588.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=27,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=20.5),
                                                  end=Point(extra={},
                                                            x=597.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=28,
                                  keyframe=False),
            VideoObjectAnnotation(name='bbox toy',
                                  feature_schema_id='ckz38ofop0mci0z9i9w3aa9o4',
                                  extra={
                                      'value': 'bbox_toy',
                                      'instanceURI': None,
                                      'color': '#1CE6FF',
                                      'feature_id': 'cl1z52xw700000fhcayaqy0ev'
                                  },
                                  value=Rectangle(extra={},
                                                  start=Point(extra={},
                                                              x=70.0,
                                                              y=19.0),
                                                  end=Point(extra={},
                                                            x=606.0,
                                                            y=348.0)),
                                  classifications=[],
                                  frame=29,
                                  keyframe=True)
        ],
        extra={
            'Created By':
                'jtso@labelbox.com',
            'Project Name':
                'Pictor Video',
            'Created At':
                '2022-04-14T15:11:19.000Z',
            'Updated At':
                '2022-04-14T15:11:21.064Z',
            'Seconds to Label':
                0.0,
            'Agreement':
                -1.0,
            'Benchmark Agreement':
                -1.0,
            'Benchmark ID':
                None,
            'Dataset Name':
                'cat',
            'Reviews': [],
            'View Label':
                'https://editor.labelbox.com?project=ckz38nsfd0lzq109bhq73est1&label=cl1z52xwh00050fhcmfgczqvn',
            'Has Open Issues':
                0.0,
            'Skipped':
                False,
            'media_type':
                'video',
            'Data Split':
                None
        })


def video_serialized_bbox_label():
    return {
        'uuid':
            'b24e672b-8f79-4d96-bf5e-b552ca0820d5',
        'dataRow': {
            'id': 'cklr9mr4m5iao0rb6cvxu4qbn'
        },
        'schemaId':
            'ckz38ofop0mci0z9i9w3aa9o4',
        'name':
            'bbox toy',
        'classifications': [],
        'segments': [{
            'keyframes': [{
                'frame': 1,
                'bbox': {
                    'top': 46.0,
                    'left': 70.0,
                    'height': 249.0,
                    'width': 384.0
                },
                'classifications': []
            }, {
                'frame': 5,
                'bbox': {
                    'top': 32.0,
                    'left': 70.0,
                    'height': 316.0,
                    'width': 277.0
                },
                'classifications': []
            }]
        }, {
            'keyframes': [{
                'frame': 9,
                'bbox': {
                    'top': 132.0,
                    'left': 70.0,
                    'height': 216.0,
                    'width': 213.0
                },
                'classifications': []
            }, {
                'frame': 15,
                'bbox': {
                    'top': 74.0,
                    'left': 70.0,
                    'height': 274.0,
                    'width': 288.0
                },
                'classifications': []
            }, {
                'frame': 21,
                'bbox': {
                    'top': 31.0,
                    'left': 70.0,
                    'height': 317.0,
                    'width': 464.0
                },
                'classifications': []
            }, {
                'frame': 29,
                'bbox': {
                    'top': 19.0,
                    'left': 70.0,
                    'height': 329.0,
                    'width': 536.0
                },
                'classifications': []
            }]
        }]
    }


def test_serialize_video_objects():
    label = video_bbox_label()
    serialized_labels = NDJsonConverter.serialize([label])
    label = next(serialized_labels)

    manual_label = video_serialized_bbox_label()

    for key in label.keys():
        # ignore uuid because we randomize if there was none
        if key != "uuid":
            assert label[key] == manual_label[key]

    assert len(label['segments']) == 2
    assert len(label['segments'][0]['keyframes']) == 2
    assert len(label['segments'][1]['keyframes']) == 4

    # #converts back only the keyframes. should be the sum of all prev segments
    deserialized_labels = NDJsonConverter.deserialize([label])
    label = next(deserialized_labels)
    assert len(label.annotations) == 6


def test_confidence_is_ignored():
    label = video_bbox_label()
    serialized_labels = NDJsonConverter.serialize([label])
    label = next(serialized_labels)
    label["confidence"] = 0.453
    label['segments'][0]["confidence"] = 0.453

    deserialized_labels = NDJsonConverter.deserialize([label])
    label = next(deserialized_labels)
    for annotation in label.annotations:
        assert annotation.confidence is None
