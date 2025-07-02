# type: ignore

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from labelbox.schema.ontology import Tool


@dataclass
class RelationshipTool(Tool):
    """
    A relationship tool to be added to a Project's ontology.

    The "tool" parameter is automatically set to Tool.Type.RELATIONSHIP
    and doesn't need to be passed during instantiation.

    The "classifications" parameter holds a list of Classification objects.
    This can be used to add nested classifications to a tool.

    Example(s):
        tool = RelationshipTool(
            name = "Relationship Tool example",
            constraints = [
                ("source_tool_feature_schema_id_1", "target_tool_feature_schema_id_1"),
                ("source_tool_feature_schema_id_2", "target_tool_feature_schema_id_2")
            ]
        )
        classification = Classification(
            class_type = Classification.Type.TEXT,
            instructions = "Classification Example")
        tool.add_classification(classification)

    Attributes:
        tool: Tool.Type.RELATIONSHIP (automatically set)
        name: (str)
        required: (bool)
        color: (str)
        classifications: (list)
        schema_id: (str)
        feature_schema_id: (str)
        attributes: (list)
        constraints: (list of [str, str])
    """

    constraints: Optional[List[Tuple[str, str]]] = None

    def __init__(
        self,
        name: str,
        constraints: Optional[List[Tuple[str, str]]] = None,
        **kwargs,
    ):
        super().__init__(Tool.Type.RELATIONSHIP, name, **kwargs)
        if constraints is not None:
            self.constraints = constraints

    def __post_init__(self):
        # Ensure tool type is set to RELATIONSHIP
        self.tool = Tool.Type.RELATIONSHIP
        super().__post_init__()

    def asdict(self) -> Dict[str, Any]:
        result = super().asdict()
        if self.constraints is not None:
            result["definition"] = {"constraints": self.constraints}
        return result

    def add_constraint(self, start: Tool, end: Tool) -> None:
        if self.constraints is None:
            self.constraints = []

        # Ensure feature schema ids are set for the tools,
        # the newly set ids will be changed during ontology creation
        # but we need to refer to the same ids in the constraints array
        # to ensure that the valid constraints are created.
        if start.feature_schema_id is None:
            start.feature_schema_id = str(uuid.uuid4())
        if start.schema_id is None:
            start.schema_id = str(uuid.uuid4())
        if end.feature_schema_id is None:
            end.feature_schema_id = str(uuid.uuid4())
        if end.schema_id is None:
            end.schema_id = str(uuid.uuid4())

        self.constraints.append(
            (start.feature_schema_id, end.feature_schema_id)
        )

    def set_constraints(self, constraints: List[Tuple[Tool, Tool]]) -> None:
        self.constraints = []
        for constraint in constraints:
            self.add_constraint(constraint[0], constraint[1])
