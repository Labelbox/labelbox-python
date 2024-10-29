from labelbox.schema.tool_building.fact_checking_tool import FactCheckingTool


def test_fact_checking_as_dict_default():
    tool = FactCheckingTool(name="Fact Checking Tool")

    # Get the dictionary representation
    tool_dict = tool.asdict()

    # Expected dictionary structure
    expected_dict = {
        "tool": "fact-checking",
        "name": "Fact Checking Tool",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
        "color": None,
        "definition": {
            "variants": [
                {"id": 0, "name": "Accurate", "actions": ["justification"]},
                {"id": 1, "name": "Inaccurate", "actions": ["justification"]},
                {"id": 2, "name": "Disputed", "actions": ["justification"]},
                {
                    "id": 3,
                    "name": "Unsupported",
                    "actions": [],
                },
                {
                    "id": 4,
                    "name": "Can't confidently assess",
                    "actions": [],
                },
                {
                    "id": 5,
                    "name": "No factual information",
                    "actions": [],
                },
            ],
            "version": 1,
        },
    }

    assert tool_dict == expected_dict


def test_step_reasoning_as_dict_with_actions():
    tool = FactCheckingTool(name="Fact Checking Tool")
    tool.set_unsupported_step_actions([])
    tool.set_cant_confidently_assess_step_actions([])
    tool.set_no_factual_information_step_actions([])

    # Get the dictionary representation
    tool_dict = tool.asdict()

    # Expected dictionary structure
    expected_dict = {
        "tool": "fact-checking",
        "name": "Fact Checking Tool",
        "required": False,
        "schemaNodeId": None,
        "featureSchemaId": None,
        "definition": {
            "variants": [
                {"id": 0, "name": "Accurate"},
                {"id": 1, "name": "Inaccurate"},
                {"id": 2, "name": "Disputed"},
                {
                    "id": 3,
                    "name": "Unsupported",
                    "actions": [],
                },
                {
                    "id": 4,
                    "name": "Can't confidently assess",
                    "actions": [],
                },
                {
                    "id": 5,
                    "name": "No factual information",
                    "actions": [],
                },
            ],
            "version": 1,
        },
    }

    assert tool_dict == expected_dict
