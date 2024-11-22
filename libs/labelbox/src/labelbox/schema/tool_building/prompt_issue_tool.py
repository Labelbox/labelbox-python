from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from labelbox.schema.tool_building.classification import (
    Classification,
    Option,
)
from labelbox.schema.tool_building.tool_type import ToolType


def _supported_classifications() -> List[Classification]:
    option_1_text = "This prompt cannot be rated (eg. contains PII, a nonsense prompt, a foreign language, or other scenario that makes the responses impossible to assess reliably). However, if you simply do not have expertise to tackle this prompt, please skip the task; do not mark it as not rateable."
    option_2_text = "This prompt contains a false, offensive, or controversial premise (eg. “why does 1+1=3”?)"
    option_3_text = "This prompt is not self-contained, i.e. the prompt cannot be understood without additional context about previous turns, account information or images."
    options = [
        Option(label=option_1_text, value="not_rateable"),
        Option(label=option_2_text, value="false_offensive_controversial"),
        Option(label=option_3_text, value="not_self_contained"),
    ]
    return [
        Classification(
            class_type=Classification.Type.CHECKLIST,
            name="prompt_issue",
            options=options,
        ),
    ]


@dataclass
class PromptIssueTool:
    """
    Use this class in OntologyBuilder to create a tool for prompt rating
    It comes with a prebuild checklist of options, which a user can modify or override
    So essentially this is a tool with a prebuilt checklist classification
    """

    name: str
    type: ToolType = field(default=ToolType.PROMPT_ISSUE, init=False)
    required: bool = False  # This attribute is for consistency with other tools and backend, default is False
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    color: Optional[str] = None
    classifications: List[Classification] = field(
        default_factory=_supported_classifications
    )

    def __post_init__(self):
        if self.name.strip() == "":
            raise ValueError("Name cannot be empty")

        if not self._validate_classifications(self.classifications):
            raise ValueError("Only one checklist classification is supported")

    def __setattr__(self, name, value):
        if name == "classifications" and not self._validate_classifications(
            value
        ):
            raise ValueError("Classifications are immutable")
        object.__setattr__(self, name, value)

    def _validate_classifications(
        self, classifications: List[Classification]
    ) -> bool:
        if (
            len(classifications) != 1
            or classifications[0].class_type != Classification.Type.CHECKLIST
            or len(classifications[0].options) < 1
        ):
            return False
        return True

    def asdict(self) -> Dict[str, Any]:
        classifications_valid = self._validate_classifications(
            self.classifications
        )
        if not classifications_valid:
            raise ValueError(
                "Classifications for Prompt Issue Tool are invalid"
            )

        return {
            "tool": self.type.value,
            "name": self.name,
            "required": self.required,
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "classifications": [
                classification.asdict()
                for classification in self.classifications
            ],
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "PromptIssueTool":
        return cls(
            name=dictionary["name"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            required=dictionary.get("required", False),
            classifications=[
                Classification.from_dict(classification)
                for classification in dictionary["classifications"]
            ],
            color=dictionary.get("color", None),
        )
