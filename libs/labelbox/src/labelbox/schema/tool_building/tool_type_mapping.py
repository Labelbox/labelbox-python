from labelbox.schema.tool_building.fact_checking_tool import (
    FactCheckingTool,
)
from labelbox.schema.tool_building.prompt_issue_tool import PromptIssueTool
from labelbox.schema.tool_building.step_reasoning_tool import (
    StepReasoningTool,
)
from labelbox.schema.tool_building.tool_type import ToolType
from labelbox.schema.ontology import Tool
from labelbox.schema.tool_building.relationship_tool import RelationshipTool


def map_tool_type_to_tool_cls(tool_type_str: str):
    # Relationship tool uses a legacy tool type, so we need to handle it separately.
    if tool_type_str.lower() == Tool.Type.RELATIONSHIP:
        return RelationshipTool()

    if not ToolType.valid(tool_type_str):
        return None

    tool_type = ToolType(tool_type_str.lower())
    if tool_type == ToolType.STEP_REASONING:
        return StepReasoningTool
    elif tool_type == ToolType.FACT_CHECKING:
        return FactCheckingTool
    elif tool_type == ToolType.PROMPT_ISSUE:
        return PromptIssueTool
