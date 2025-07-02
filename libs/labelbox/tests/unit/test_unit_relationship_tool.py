import uuid
from unittest.mock import patch

from labelbox.schema.ontology import Tool
from labelbox.schema.tool_building.relationship_tool import RelationshipTool


def test_basic_instantiation():
    tool = RelationshipTool(name="Test Relationship Tool")

    assert tool.name == "Test Relationship Tool"
    assert tool.tool == Tool.Type.RELATIONSHIP
    assert tool.constraints is None
    assert tool.required is False
    assert tool.color is None
    assert tool.schema_id is None
    assert tool.feature_schema_id is None


def test_instantiation_with_constraints():
    constraints = [
        ("source_id_1", "target_id_1"),
        ("source_id_2", "target_id_2"),
    ]
    tool = RelationshipTool(name="Test Tool", constraints=constraints)

    assert tool.name == "Test Tool"
    assert tool.constraints == constraints
    assert len(tool.constraints) == 2


def test_post_init_sets_tool_type():
    tool = RelationshipTool(name="Test Tool")
    assert tool.tool == Tool.Type.RELATIONSHIP


def test_asdict_without_constraints():
    tool = RelationshipTool(name="Test Tool", required=True, color="#FF0000")

    result = tool.asdict()
    expected = {
        "tool": "edge",
        "name": "Test Tool",
        "required": True,
        "color": "#FF0000",
        "classifications": [],
        "schemaNodeId": None,
        "featureSchemaId": None,
        "attributes": None,
    }

    assert result == expected


def test_asdict_with_constraints():
    constraints = [("source_id", "target_id")]
    tool = RelationshipTool(name="Test Tool", constraints=constraints)

    result = tool.asdict()

    assert "definition" in result
    assert result["definition"] == {"constraints": constraints}
    assert result["tool"] == "edge"
    assert result["name"] == "Test Tool"


def test_add_constraint_to_empty_constraints():
    tool = RelationshipTool(name="Test Tool")
    start_tool = Tool(Tool.Type.BBOX, "Start Tool")
    end_tool = Tool(Tool.Type.POLYGON, "End Tool")

    with patch("uuid.uuid4") as mock_uuid:
        mock_uuid.return_value.hex = "test-uuid"
        tool.add_constraint(start_tool, end_tool)

    assert tool.constraints is not None
    assert len(tool.constraints) == 1
    assert start_tool.feature_schema_id is not None
    assert start_tool.schema_id is not None
    assert end_tool.feature_schema_id is not None
    assert end_tool.schema_id is not None


def test_add_constraint_to_existing_constraints():
    existing_constraints = [("existing_source", "existing_target")]
    tool = RelationshipTool(name="Test Tool", constraints=existing_constraints)

    start_tool = Tool(Tool.Type.BBOX, "Start Tool")
    end_tool = Tool(Tool.Type.POLYGON, "End Tool")

    tool.add_constraint(start_tool, end_tool)

    assert len(tool.constraints) == 2
    assert tool.constraints[0] == ("existing_source", "existing_target")
    assert tool.constraints[1] == (
        start_tool.feature_schema_id,
        end_tool.feature_schema_id,
    )


def test_add_constraint_preserves_existing_ids():
    tool = RelationshipTool(name="Test Tool")
    start_tool_feature_schema_id = "start_tool_feature_schema_id"
    start_tool_schema_id = "start_tool_schema_id"
    start_tool = Tool(
        Tool.Type.BBOX,
        "Start Tool",
        feature_schema_id=start_tool_feature_schema_id,
        schema_id=start_tool_schema_id,
    )
    end_tool_feature_schema_id = "end_tool_feature_schema_id"
    end_tool_schema_id = "end_tool_schema_id"
    end_tool = Tool(
        Tool.Type.POLYGON,
        "End Tool",
        feature_schema_id=end_tool_feature_schema_id,
        schema_id=end_tool_schema_id,
    )

    tool.add_constraint(start_tool, end_tool)

    assert start_tool.feature_schema_id == start_tool_feature_schema_id
    assert start_tool.schema_id == start_tool_schema_id
    assert end_tool.feature_schema_id == end_tool_feature_schema_id
    assert end_tool.schema_id == end_tool_schema_id
    assert tool.constraints == [
        (start_tool_feature_schema_id, end_tool_feature_schema_id)
    ]


def test_set_constraints():
    tool = RelationshipTool(name="Test Tool")

    start_tool1 = Tool(Tool.Type.BBOX, "Start Tool 1")
    end_tool1 = Tool(Tool.Type.POLYGON, "End Tool 1")
    start_tool2 = Tool(Tool.Type.POINT, "Start Tool 2")
    end_tool2 = Tool(Tool.Type.LINE, "End Tool 2")

    tool.set_constraints([(start_tool1, end_tool1), (start_tool2, end_tool2)])

    assert len(tool.constraints) == 2
    assert tool.constraints[0] == (
        start_tool1.feature_schema_id,
        end_tool1.feature_schema_id,
    )
    assert tool.constraints[1] == (
        start_tool2.feature_schema_id,
        end_tool2.feature_schema_id,
    )


def test_set_constraints_replaces_existing():
    existing_constraints = [("old_source", "old_target")]
    tool = RelationshipTool(name="Test Tool", constraints=existing_constraints)

    start_tool = Tool(Tool.Type.BBOX, "Start Tool")
    end_tool = Tool(Tool.Type.POLYGON, "End Tool")

    tool.set_constraints([(start_tool, end_tool)])

    assert len(tool.constraints) == 1
    assert tool.constraints[0] != ("old_source", "old_target")
    assert tool.constraints[0] == (
        start_tool.feature_schema_id,
        end_tool.feature_schema_id,
    )


def test_uuid_generation_in_add_constraint():
    tool = RelationshipTool(name="Test Tool")

    start_tool = Tool(Tool.Type.BBOX, "Start Tool")
    end_tool = Tool(Tool.Type.POLYGON, "End Tool")

    # Ensure tools don't have IDs initially
    assert start_tool.feature_schema_id is None
    assert start_tool.schema_id is None
    assert end_tool.feature_schema_id is None
    assert end_tool.schema_id is None

    tool.add_constraint(start_tool, end_tool)

    # Check that UUIDs were generated
    assert start_tool.feature_schema_id is not None
    assert start_tool.schema_id is not None
    assert end_tool.feature_schema_id is not None
    assert end_tool.schema_id is not None

    # Check that they are valid UUID strings
    uuid.UUID(start_tool.feature_schema_id)  # Will raise ValueError if invalid
    uuid.UUID(start_tool.schema_id)
    uuid.UUID(end_tool.feature_schema_id)
    uuid.UUID(end_tool.schema_id)


def test_constraints_in_asdict():
    tool = RelationshipTool(name="Test Tool")

    start_tool = Tool(Tool.Type.BBOX, "Start Tool")
    end_tool = Tool(Tool.Type.POLYGON, "End Tool")

    tool.add_constraint(start_tool, end_tool)

    result = tool.asdict()

    assert "definition" in result
    assert "constraints" in result["definition"]
    assert len(result["definition"]["constraints"]) == 1
    assert result["definition"]["constraints"][0] == (
        start_tool.feature_schema_id,
        end_tool.feature_schema_id,
    )
