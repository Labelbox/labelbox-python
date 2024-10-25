from labelbox.schema.tool_building.base_step_reasoning_tool import _Variant


def test_variant():
    variant = _Variant(
        id=0, name="Correct", _available_actions={"regenerateSteps"}
    )
    variant.set_actions(["regenerateSteps"])
    assert variant.asdict() == {
        "id": 0,
        "name": "Correct",
        "actions": ["regenerateSteps"],
    }

    assert variant._available_actions == {"regenerateSteps"}
    variant.reset_actions()
    assert variant.asdict() == {
        "id": 0,
        "name": "Correct",
        "actions": [],
    }


def test_variant_actions():
    variant = _Variant(
        id=0, name="Correct", _available_actions={"regenerateSteps"}
    )
    variant.set_actions(["regenerateSteps"])
    assert variant.actions == ["regenerateSteps"]
    variant.set_actions(["invalidAction"])
    assert variant.actions == []
