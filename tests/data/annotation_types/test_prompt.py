from labelbox.data.annotation_types.classification.classification import ClassificationAnnotation, Prompt, Text
from labelbox.data.annotation_types.data.llm_prompt_creation import LlmPromptCreationData
from labelbox.data.annotation_types.label import Label
from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_prompt():
    prompt_annotation = ClassificationAnnotation(
    name="Provide a prompt",
    value=Text(answer="This is a MAL prompt"),
    )

    label = []
    label.append(
    Label(
        data=LlmPromptCreationData(
            global_key="clnwyvqhh01l7hnvugsmqb1et"
        ),
        annotations=[
        prompt_annotation,
        ]
    )
    )
  
    expected_serialized = {'name': 'Provide a prompt', 'answer': 'This is a MAL prompt', 'dataRow': {'globalKey': 'clnwyvqhh01l7hnvugsmqb1et'}}
    serialized = list(NDJsonConverter.serialize(label))
    actual = serialized[0]
    actual.pop('uuid')
    assert actual == expected_serialized
    res = list(NDJsonConverter.deserialize(serialized))
    assert res == label