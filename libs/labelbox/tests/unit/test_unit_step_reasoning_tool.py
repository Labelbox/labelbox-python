from labelbox.schema.tool_building.step_reasoning_tool import StepReasoningTool


def test_step_reasoning_as_dict_default():
    tool = StepReasoningTool(name="step reasoning")
    assert tool.asdict() == {
        "tool": "step-reasoning",
        "name": "step reasoning",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
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


def test_step_reasoning_as_dict_with_actions():
    tool = StepReasoningTool(name="step reasoning")
    tool.reset_generate_and_rate_alternative_steps()
    tool.reset_regenerate_steps()
    tool.reset_rewrite_step()
    tool.reset_justification()
    assert tool.asdict() == {
        "tool": "step-reasoning",
        "name": "step reasoning",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
        "definition": {
            "variants": [
                {"id": 0, "name": "Correct", "actions": []},
                {"id": 1, "name": "Neutral", "actions": []},
                {
                    "id": 2,
                    "name": "Incorrect",
                    "actions": [],
                },
            ],
            "version": 1,
        },
    }
