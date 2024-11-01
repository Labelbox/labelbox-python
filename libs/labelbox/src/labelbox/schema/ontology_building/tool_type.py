from enum import Enum


class ToolType(Enum):
    STEP_REASONING = "step-reasoning"
    FACT_CHECKING = "fact-checking"
    PROMPT_ISSUE = "prompt-issue"

    @classmethod
    def valid(cls, tool_type: str) -> bool:
        try:
            ToolType(tool_type.lower())
            return True
        except ValueError:
            return False
