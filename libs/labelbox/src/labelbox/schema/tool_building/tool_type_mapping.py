from labelbox.schema.tool_building.fact_checking_tool import (
    FactCheckingTool,
)
from labelbox.schema.tool_building.prompt_issue_tool import PromptIssueTool
from labelbox.schema.tool_building.step_reasoning_tool import (
    StepReasoningTool,
)
from labelbox.schema.tool_building.tool_type import ToolType


def map_tool_type_to_tool_cls(tool_type_str: str):
    if not ToolType.valid(tool_type_str):
        return None

    tool_type = ToolType(tool_type_str.lower())
    if tool_type == ToolType.STEP_REASONING:
        return StepReasoningTool
    elif tool_type == ToolType.FACT_CHECKING:
        return FactCheckingTool
    elif tool_type == ToolType.PROMPT_ISSUE:
        return PromptIssueTool
