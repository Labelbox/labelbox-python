from labelbox.schema.tool_building.step_reasoning_tool import StepReasoningTool


def test_step_reasoning_as_dict_default():
    tool = StepReasoningTool(name="step reasoning")
    assert tool.asdict() == {
        "tool": "step-reasoning",
        "name": "step reasoning",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
        "variants": [
            {"id": 0, "name": "Correct"},
            {"id": 1, "name": "Neutral"},
            {"id": 2, "name": "Incorrect", "actions": []},
        ],
    }


def test_step_reasoning_as_dict_with_actions():
    tool = StepReasoningTool(name="step reasoning")
    tool.set_rate_alternative_responses()
    tool.set_regenerate_conversations_after_incorrect_step()
    assert tool.asdict() == {
        "tool": "step-reasoning",
        "name": "step reasoning",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
        "variants": [
            {"id": 0, "name": "Correct"},
            {"id": 1, "name": "Neutral"},
            {
                "id": 2,
                "name": "Incorrect",
                "actions": ["regenerateSteps", "generateAlternatives"],
            },
        ],
    }
