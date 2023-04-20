import pytest


@pytest.fixture()
def expected_export_v2_image():
    exported_annotations = {
        'objects': [{
            'name':
                'polygon',
            'annotation_kind':
                'ImagePolygon',
            'classifications': [],
            'polygon': [{
                'x': 147.692,
                'y': 118.154
            }, {
                'x': 142.769,
                'y': 104.923
            }, {
                'x': 57.846,
                'y': 118.769
            }, {
                'x': 28.308,
                'y': 169.846
            }, {
                'x': 147.692,
                'y': 118.154
            }]
        }, {
            'name': 'bbox',
            'annotation_kind': 'ImageBoundingBox',
            'classifications': [{
                'name': 'nested',
                'radio_answer': {
                    'name': 'radio_option_1',
                    'classifications': []
                }
            }],
            'bounding_box': {
                'top': 48.0,
                'left': 58.0,
                'height': 65.0,
                'width': 12.0
            }
        }, {
            'name': 'polyline',
            'annotation_kind': 'ImageLine',
            'classifications': [],
            'line': [{
                'x': 147.692,
                'y': 118.154
            }, {
                'x': 150.692,
                'y': 160.154
            }]
        }],
        'classifications': [{
            'name': 'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }

    return exported_annotations


@pytest.fixture()
def expected_export_v2_audio():
    expected_annotations = {
        'objects': [],
        'classifications': [{
            'name': 'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_html():
    expected_annotations = {
        'objects': [],
        'classifications': [{
            'name': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }, {
            'name': 'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'classifications': []
            }]
        }],
        'relationships': []
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_text():
    expected_annotations = {
        'objects': [{
            'name': 'named-entity',
            'annotation_kind': 'TextEntity',
            'classifications': [],
            'location': {
                'start': 67,
                'end': 128
            }
        }],
        'classifications': [{
            'name': 'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_video():
    expected_annotations = {
        'frames': {},
        'segments': {},
        'key_frame_feature_map': {},
        'classifications': [{
            'name': 'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'classifications': []
            }]
        }]
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_conversation():
    expected_annotations = {
        'objects': [{
            'name': 'named-entity',
            'annotation_kind': 'ConversationalTextEntity',
            'classifications': [],
            'conversational_location': {
                'message_id': '0',
                'location': {
                    'start': 0,
                    'end': 8
                }
            }
        }],
        'classifications': [],
        'relationships': []
    }
    return expected_annotations
