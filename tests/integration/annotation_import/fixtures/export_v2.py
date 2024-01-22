import pytest


@pytest.fixture()
def expected_export_v2_image():
    exported_annotations = {
        'objects': [{
            'name':
                'polygon',
            'value':
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
            'value': 'bbox',
            'annotation_kind': 'ImageBoundingBox',
            'classifications': [{
                'name': 'nested',
                'value': 'nested',
                'radio_answer': {
                    'name': 'radio_option_1',
                    'value': 'radio_value_1',
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
            'value': 'polyline',
            'annotation_kind': 'ImagePolyline',
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
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'value': 'text',
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
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'value': 'text',
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
            'value': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }, {
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
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
            'value': 'named_entity',
            'annotation_kind': 'TextEntity',
            'classifications': [],
            'location': {
                'start': 67,
                'end': 128
            }
        }],
        'classifications': [{
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'value': 'text',
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
        'segments': {
            '<cuid>': [[7, 13], [18, 19]]
        },
        'key_frame_feature_map': {},
        'classifications': [{
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
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
            'value': 'named_entity',
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
        'classifications': [{
            'name':
                'checklist_index',
            'value':
                'checklist_index',
            'message_id':
                '0',
            'conversational_checklist_answers': [{
                'name': 'option1_index',
                'value': 'option1_index',
                'classifications': []
            }]
        }, {
            'name': 'text_index',
            'value': 'text_index',
            'message_id': '0',
            'conversational_text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_dicom():
    expected_annotations = {
        'groups': {
            'Axial': {
                'name': 'Axial',
                'classifications': [],
                'frames': {
                    '1': {
                        'objects': {
                            '<cuid>': {
                                'name':
                                    'polyline',
                                'value':
                                    'polyline',
                                'annotation_kind':
                                    'DICOMPolyline',
                                'classifications': [],
                                'line': [{
                                    'x': 147.692,
                                    'y': 118.154
                                }, {
                                    'x': 150.692,
                                    'y': 160.154
                                }]
                            }
                        },
                        'classifications': []
                    }
                }
            },
            'Sagittal': {
                'name': 'Sagittal',
                'classifications': [],
                'frames': {}
            },
            'Coronal': {
                'name': 'Coronal',
                'classifications': [],
                'frames': {}
            }
        },
        'segments': {
            'Axial': {
                '<cuid>': [[1, 1]]
            },
            'Sagittal': {},
            'Coronal': {}
        },
        'classifications': [],
        'key_frame_feature_map': {
            '<cuid>': {
                'Axial': {
                    '1': True
                },
                'Coronal': {},
                'Sagittal': {}
            }
        }
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_document():
    expected_annotations = {
        'objects': [{
            'name': 'named-entity',
            'value': 'named_entity',
            'annotation_kind': 'DocumentEntityToken',
            'classifications': [],
            'location': {
                'groups': [{
                    'id':
                        '2f4336f4-a07e-4e0a-a9e1-5629b03b719b',
                    'page_number':
                        1,
                    'tokens': [
                        '3f984bf3-1d61-44f5-b59a-9658a2e3440f',
                        '3bf00b56-ff12-4e52-8cc1-08dbddb3c3b8',
                        '6e1c3420-d4b7-4c5a-8fd6-ead43bf73d80',
                        '87a43d32-af76-4a1d-b262-5c5f4d5ace3a',
                        'e8606e8a-dfd9-4c49-a635-ad5c879c75d0',
                        '67c7c19e-4654-425d-bf17-2adb8cf02c30',
                        '149c5e80-3e07-49a7-ab2d-29ddfe6a38fa',
                        'b0e94071-2187-461e-8e76-96c58738a52c'
                    ],
                    'text':
                        'Metal-insulator (MI) transitions have been one of the'
                }]
            }
        }, {
            'name': 'bbox',
            'value': 'bbox',
            'annotation_kind': 'DocumentBoundingBox',
            'classifications': [{
                'name': 'nested',
                'value': 'nested',
                'radio_answer': {
                    'name': 'radio_option_1',
                    'value': 'radio_value_1',
                    'classifications': []
                }
            }],
            'page_number': 1,
            'bounding_box': {
                'top': 48.0,
                'left': 58.0,
                'height': 65.0,
                'width': 12.0
            }
        }],
        'classifications': [{
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'value': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_llm_prompt_creation():
    expected_annotations = {
        'objects': [],
        'classifications': [{
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'value': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_llm_prompt_response_creation():
    expected_annotations = {
        'objects': [],
        'classifications': [{
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'value': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }
    return expected_annotations


@pytest.fixture()
def expected_export_v2_llm_response_creation():
    expected_annotations = {
        'objects': [],
        'classifications': [{
            'name':
                'checklist',
            'value':
                'checklist',
            'checklist_answers': [{
                'name': 'option1',
                'value': 'option1',
                'classifications': []
            }]
        }, {
            'name': 'text',
            'value': 'text',
            'text_answer': {
                'content': 'free form text...'
            }
        }],
        'relationships': []
    }
    return expected_annotations
