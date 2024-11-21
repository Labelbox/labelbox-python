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
    for variant in tool.definition.variants:
        variant.set_actions([])

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
                {"id": 0, "name": "Accurate", "actions": []},
                {"id": 1, "name": "Inaccurate", "actions": []},
                {"id": 2, "name": "Disputed", "actions": []},
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
