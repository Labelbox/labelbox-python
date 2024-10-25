import pytest

from labelbox.schema.tool_building.step_reasoning_tool import (
    StepReasoningTool,
)


def test_validations():
    with pytest.raises(ValueError):
        StepReasoningTool(name="")


def test_step_reasoning_as_dict_default():
    tool = StepReasoningTool(name="step reasoning")
    assert tool.definition.variants[2]._available_actions == {
        "regenerateSteps",
        "generateAndRateAlternativeSteps",
        "rewriteStep",
        "justification",
    }

    assert tool.asdict() == {
        "tool": "step-reasoning",
        "name": "step reasoning",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
        "color": None,
        "definition": {
            "variants": [
                {"id": 0, "name": "Correct", "actions": []},
                {"id": 1, "name": "Neutral", "actions": []},
                {
                    "id": 2,
                    "name": "Incorrect",
                    "actions": [
                        "regenerateSteps",
                        "generateAndRateAlternativeSteps",
                        "rewriteStep",
                        "justification",
                    ],
                },
            ],
            "version": 1,
        },
    }


def test_from_dict():
    dict = {
        "schemaNodeId": "cm3pdkupv0ah8070h2ujo74th",
        "featureSchemaId": "cm3pdkupv0ah7070hg7svdeeo",
        "required": False,
        "name": "step reasoning",
        "tool": "step-reasoning",
        "definition": {
            "variants": [
                {"id": 0, "name": "Correct", "actions": []},
                {"id": 1, "name": "Neutral", "actions": []},
                {
                    "id": 2,
                    "name": "Incorrect",
                    "actions": [
                        "regenerateSteps",
                        "generateAndRateAlternativeSteps",
                        "rewriteStep",
                        "justification",
                    ],
                },
            ],
            "version": 1,
            "title": "step reasoning",
            "value": "step_reasoning",
            "color": "#ff0000",
        },
        "color": "#ff0000",
        "archived": 0,
        "classifications": [],
        "kind": "StepReasoning",
    }
    tool = StepReasoningTool.from_dict(dict)
    assert tool.definition.variants[2]._available_actions == {
        "generateAndRateAlternativeSteps",
        "justification",
        "rewriteStep",
        "regenerateSteps",
    }
