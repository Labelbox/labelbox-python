import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
    regenerate_conversations_after_incorrect_step: Optional[bool] = True
    rate_alternative_responses: Optional[bool] = False

    def asdict(self) -> Dict[str, Any]:
        actions = []
        if self.regenerate_conversations_after_incorrect_step:
            actions.append("regenerateSteps")
        if self.rate_alternative_responses:
            actions.append("generateAndRateAlternativeSteps")
        return {"id": self.id, "name": self.name, "actions": actions}

    @classmethod
    def from_dict(
        cls, dictionary: Dict[str, Any]
    ) -> "IncorrectStepReasoningVariant":
        return cls(
            id=dictionary["id"],
            name=dictionary["name"],
            regenerate_conversations_after_incorrect_step="regenerateSteps"
            in dictionary.get("actions", []),
            rate_alternative_responses="generateAndRateAlternativeSteps"
            in dictionary.get("actions", []),
        )


def _create_correct_step() -> StepReasoningVariant:
    return StepReasoningVariant(
        id=StepReasoningVariants.CORRECT_STEP_ID, name="Correct"
    )


def _create_neutral_step() -> StepReasoningVariant:
    return StepReasoningVariant(
        id=StepReasoningVariants.NEUTRAL_STEP_ID, name="Neutral"
    )


def _create_incorrect_step() -> IncorrectStepReasoningVariant:
    return IncorrectStepReasoningVariant(
        id=StepReasoningVariants.INCORRECT_STEP_ID, name="Incorrect"
    )


@dataclass
class StepReasoningVariants:
    """
    This class is used to define the possible options for evaluating a step
    Currently the options are correct, neutral, and incorrect
    """

    CORRECT_STEP_ID = 0
    NEUTRAL_STEP_ID = 1
    INCORRECT_STEP_ID = 2

    correct_step: StepReasoningVariant = field(
        default_factory=_create_correct_step
    )
    neutral_step: StepReasoningVariant = field(
        default_factory=_create_neutral_step
    )
    incorrect_step: IncorrectStepReasoningVariant = field(
        default_factory=_create_incorrect_step
    )

    def asdict(self):
        return [
            self.correct_step.asdict(),
            self.neutral_step.asdict(),
            self.incorrect_step.asdict(),
        ]

    @classmethod
    def from_dict(cls, dictionary: List[Dict[str, Any]]):
        correct_step = None
        neutral_step = None
        incorrect_step = None

        for variant in dictionary:
            if variant["id"] == cls.CORRECT_STEP_ID:
                correct_step = StepReasoningVariant(**variant)
            elif variant["id"] == cls.NEUTRAL_STEP_ID:
                neutral_step = StepReasoningVariant(**variant)
            elif variant["id"] == cls.INCORRECT_STEP_ID:
                incorrect_step = IncorrectStepReasoningVariant.from_dict(
                    variant
                )

        if not all([correct_step, neutral_step, incorrect_step]):
            raise ValueError("Invalid step reasoning variants")

        return cls(
            correct_step=correct_step,  # type: ignore
            neutral_step=neutral_step,  # type: ignore
            incorrect_step=incorrect_step,  # type: ignore
        )


@dataclass
class StepReasoningDefinition:
    variants: StepReasoningVariants = field(
        default_factory=StepReasoningVariants
    )
    version: int = field(default=1)
    title: Optional[str] = None
    value: Optional[str] = None

    def asdict(self) -> Dict[str, Any]:
        result = {"variants": self.variants.asdict(), "version": self.version}
        if self.title is not None:
            result["title"] = self.title
        if self.value is not None:
            result["value"] = self.value
        return result

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "StepReasoningDefinition":
        variants = StepReasoningVariants.from_dict(dictionary["variants"])
        title = dictionary.get("title", None)
        value = dictionary.get("value", None)
        return cls(variants=variants, title=title, value=value)


@dataclass
class StepReasoningTool:
    """
    Use this class in OntologyBuilder to create a tool for step reasoning
    The definition field lists the possible options to evaulate a step
    """

    name: str
    type: ToolType = field(default=ToolType.STEP_REASONING, init=False)
    required: bool = False
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    color: Optional[str] = None
    definition: StepReasoningDefinition = field(
        default_factory=StepReasoningDefinition
    )

    def __post_init__(self):
        warnings.warn(
            "This feature is experimental and subject to change.",
        )

    def reset_regenerate_conversations_after_incorrect_step(self):
        """
        For live models, the default acation will invoke the model to generate alternatives if a step is marked as incorrect
        This method will reset the action to not regenerate the conversation
        """
        self.definition.variants.incorrect_step.regenerate_conversations_after_incorrect_step = False

    def set_rate_alternative_responses(self):
        """
        For live models, will require labelers to rate the alternatives generated by the model
        """
        self.definition.variants.incorrect_step.rate_alternative_responses = (
            True
        )

    def asdict(self) -> Dict[str, Any]:
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
            definition=StepReasoningDefinition.from_dict(
                dictionary["definition"]
            ),
        )
