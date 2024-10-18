from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from labelbox.schema.tool_building.tool_type import ToolType


@dataclass
class StepReasoningVariant:
    id: int
    name: str

    def asdict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name}


@dataclass
class IncorrectStepReasoningVariant:
    id: int
    name: str
    regenerate_conversations_after_incorrect_step: Optional[bool] = False
    rate_alternative_responses: Optional[bool] = False

    def asdict(self) -> Dict[str, Any]:
        actions = []
        if self.regenerate_conversations_after_incorrect_step:
            actions.append("regenerateSteps")
        if self.rate_alternative_responses:
            actions.append("generateAlternatives")
        return {"id": self.id, "name": self.name, "actions": actions}


@dataclass
class StepReasoningVariants:
    CORRECT_STEP_ID = 0
    NEUTRAL_STEP_ID = 1
    INCORRECT_STEP_ID = 2

    correct_step: StepReasoningVariant = field(
        default=StepReasoningVariant(CORRECT_STEP_ID, "Correct"), init=False
    )
    neutral_step: StepReasoningVariant = field(
        default=StepReasoningVariant(NEUTRAL_STEP_ID, "Neutral"), init=False
    )
    incorrect_step: IncorrectStepReasoningVariant = field(
        default=IncorrectStepReasoningVariant(INCORRECT_STEP_ID, "Incorrect"),
    )

    def asdict(self):
        return [
            self.correct_step.asdict(),
            self.neutral_step.asdict(),
            self.incorrect_step.asdict(),
        ]


@dataclass
class StepReasoningDefinition:
    variants: StepReasoningVariants = field(
        default_factory=StepReasoningVariants
    )
    version: int = field(default=1)
    title: Optional[str] = None
    value: Optional[str] = None
    color: Optional[str] = None

    def asdict(self) -> Dict[str, Any]:
        result = {"variants": self.variants.asdict(), "version": self.version}
        if self.title is not None:
            result["title"] = self.title
        if self.value is not None:
            result["value"] = self.value
        if self.color is not None:
            result["color"] = self.color
        return result


@dataclass
class StepReasoningTool:
    name: str
    type: ToolType = field(default=ToolType.STEP_REASONING, init=False)
    required: bool = False
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    color: Optional[str] = None
    definition: StepReasoningDefinition = field(
        default_factory=StepReasoningDefinition
    )

    def set_regenerate_conversations_after_incorrect_step(self):
        self.definition.variants.incorrect_step.regenerate_conversations_after_incorrect_step = True

    def set_rate_alternative_responses(self):
        self.definition.variants.incorrect_step.rate_alternative_responses = (
            True
        )

    def asdict(self) -> Dict[str, Any]:
        self.set_rate_alternative_responses()
        self.set_regenerate_conversations_after_incorrect_step()
        return {
            "tool": self.type.value,
            "name": self.name,
            "required": self.required,
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "definition": self.definition.asdict(),
        }

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "StepReasoningTool":
        return cls(
            name=dictionary["name"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            required=dictionary.get("required", False),
            definition=StepReasoningDefinition(**dictionary["definition"]),
        )
