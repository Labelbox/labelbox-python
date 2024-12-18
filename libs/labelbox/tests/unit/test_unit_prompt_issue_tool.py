import pytest

from labelbox.schema.tool_building.classification import Classification
from labelbox.schema.tool_building.prompt_issue_tool import PromptIssueTool


def test_as_dict():
    tool = PromptIssueTool(name="Prompt Issue Tool")

    # Get the dictionary representation
    tool_dict = tool.asdict()
    expected_dict = {
        "tool": "prompt-issue",
        "name": "Prompt Issue Tool",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
        "classifications": [
            {
                "type": "checklist",
                "instructions": "prompt_issue",
                "name": "prompt_issue",
                "required": False,
                "options": [
                    {
                        "schemaNodeId": None,
                        "featureSchemaId": None,
                        "label": "This prompt cannot be rated (eg. contains PII, a nonsense prompt, a foreign language, or other scenario that makes the responses impossible to assess reliably). However, if you simply do not have expertise to tackle this prompt, please skip the task; do not mark it as not rateable.",
                        "value": "not_rateable",
                        "options": [],
                    },
                    {
                        "schemaNodeId": None,
                        "featureSchemaId": None,
                        "label": "This prompt contains a false, offensive, or controversial premise (eg. “why does 1+1=3”?)",
                        "value": "false_offensive_controversial",
                        "options": [],
                    },
                    {
                        "schemaNodeId": None,
                        "featureSchemaId": None,
                        "label": "This prompt is not self-contained, i.e. the prompt cannot be understood without additional context about previous turns, account information or images.",
                        "value": "not_self_contained",
                        "options": [],
                    },
                ],
                "schemaNodeId": None,
                "featureSchemaId": None,
                "scope": "global",
                "attributes": None,
            }
        ],
        "color": None,
    }
    assert tool_dict == expected_dict


def test_classification_validation():
    tool = PromptIssueTool(name="Prompt Issue Tool")
    with pytest.raises(ValueError):
        tool.classifications = [
            Classification(Classification.Type.TEXT, "prompt_issue")
        ]

    with pytest.raises(ValueError):
        tool.classifications = "abcd"

    # Test that we can modify the classification options
    classification = tool.classifications[0]
    classification.options.pop()
    classification.options[0].label = "test"
    classification.options[0].value == "test_value"
    tool.classifications = [classification]
    assert tool.classifications == [classification]
