import json

import pytest
import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter

radio_ndjson = [{
    'dataRow': {
        'globalKey': 'my_global_key'
    },
    'name': 'radio',
    'answer': {
        'name': 'first_radio_answer'
    },
    'messageId': '0'
}]

radio_label = [
    lb_types.Label(
        data=lb_types.ConversationData(global_key='my_global_key'),
        annotations=[
            lb_types.ClassificationAnnotation(
                name='radio',
                value=lb_types.Radio(answer=lb_types.ClassificationAnswer(
                    name="first_radio_answer")),
                message_id="0")
        ])
]

checklist_ndjson = [{
    'dataRow': {
        'globalKey': 'my_global_key'
    },
    'name': 'checklist',
    'answer': [
        {
            'name': 'first_checklist_answer'
        },
        {
            'name': 'second_checklist_answer'
        },
    ],
    'messageId': '2'
}]

checklist_label = [
    lb_types.Label(data=lb_types.ConversationData(global_key='my_global_key'),
                   annotations=[
                       lb_types.ClassificationAnnotation(
                           name='checklist',
                           message_id="2",
                           value=lb_types.Checklist(answer=[
                               lb_types.ClassificationAnswer(
                                   name="first_checklist_answer"),
                               lb_types.ClassificationAnswer(
                                   name="second_checklist_answer")
                           ]))
                   ])
]

free_text_ndjson = [{
    'dataRow': {
        'globalKey': 'my_global_key'
    },
    'name': 'free_text',
    'answer': 'sample text',
    'messageId': '0'
}]
free_text_label = [
    lb_types.Label(data=lb_types.ConversationData(global_key='my_global_key'),
                   annotations=[
                       lb_types.ClassificationAnnotation(
                           name='free_text',
                           message_id="0",
                           value=lb_types.Text(answer="sample text"))
                   ])
]


@pytest.mark.parametrize(
    "label, ndjson",
    [[radio_label, radio_ndjson], [checklist_label, checklist_ndjson],
     [free_text_label, free_text_ndjson]])
def test_message_based_radio_classification(label, ndjson):
    serialized_label = list(NDJsonConverter().serialize(label))
    serialized_label[0].pop('uuid')
    assert serialized_label == ndjson

    deserialized_label = list(NDJsonConverter().deserialize(ndjson))
    deserialized_label[0].annotations[0].extra.pop('uuid')
    assert deserialized_label[0].annotations == label[0].annotations


@pytest.mark.parametrize("filename", [
    "tests/data/assets/ndjson/conversation_entity_import.json",
    "tests/data/assets/ndjson/conversation_entity_without_confidence_import.json"
])
def test_conversation_entity_import(filename: str):
    with open(filename, 'r') as file:
        data = json.load(file)
    res = list(NDJsonConverter.deserialize(data))
    res = list(NDJsonConverter.serialize(res))
    assert res == data


def test_benchmark_reference_label_flag_enabled():
    label = lb_types.Label(data=lb_types.ConversationData(global_key='my_global_key'),
                   annotations=[
                       lb_types.ClassificationAnnotation(
                           name='free_text',
                           message_id="0",
                           value=lb_types.Text(answer="sample text"))
                   ],
                   is_benchmark_reference=True
                   )

    res = list(NDJsonConverter.serialize([label]))
    assert res[0]["isBenchmarkReferenceLabel"]


def test_benchmark_reference_label_flag_disabled():
    label = lb_types.Label(data=lb_types.ConversationData(global_key='my_global_key'),
                   annotations=[
                       lb_types.ClassificationAnnotation(
                           name='free_text',
                           message_id="0",
                           value=lb_types.Text(answer="sample text"))
                   ],
                   is_benchmark_reference=False
                   )

    res = list(NDJsonConverter.serialize([label]))
    assert not res[0].get("isBenchmarkReferenceLabel")
