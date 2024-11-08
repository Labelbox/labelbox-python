import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from labelbox.schema.tool_building.tool_type import ToolType


@dataclass
class StepReasoningVariant:
    id: int
    name: str
    actions: List[str] = field(default_factory=list)

    def asdict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "actions": self.actions}


@dataclass
class IncorrectStepReasoningVariant:
    id: int
    name: str
    regenerate_steps: Optional[bool] = True
    generate_and_rate_alternative_steps: Optional[bool] = True
    rewrite_step: Optional[bool] = True
    justification: Optional[bool] = True

    def asdict(self) -> Dict[str, Any]:
        actions = []
        if self.regenerate_steps:
            actions.append("regenerateSteps")
        if self.generate_and_rate_alternative_steps:
            actions.append("generateAndRateAlternativeSteps")
        if self.rewrite_step:
            actions.append("rewriteStep")
        if self.justification:
            actions.append("justification")
        return {"id": self.id, "name": self.name, "actions": actions}

    @classmethod
    def from_dict(
        cls, dictionary: Dict[str, Any]
    ) -> "IncorrectStepReasoningVariant":
        return cls(
            id=dictionary["id"],
            name=dictionary["name"],
            regenerate_steps="regenerateSteps" in dictionary.get("actions", []),
            generate_and_rate_alternative_steps="generateAndRateAlternativeSteps"
            in dictionary.get("actions", []),
            rewrite_step="rewriteStep" in dictionary.get("actions", []),
            justification="justification" in dictionary.get("actions", []),
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

    def reset_regenerate_steps(self):
        """
        For live models, the default acation will invoke the model to generate alternatives if a step is marked as incorrect
        This method will reset the action to not regenerate the conversation
        """
        self.definition.variants.incorrect_step.regenerate_steps = False

    def reset_generate_and_rate_alternative_steps(self):
        """
        For live models, will require labelers to rate the alternatives generated by the model
        """
        self.definition.variants.incorrect_step.generate_and_rate_alternative_steps = False

    def reset_rewrite_step(self):
        """
        For live models, will require labelers to rewrite the conversation
        """
        self.definition.variants.incorrect_step.rewrite_step = False

    def reset_justification(self):
        """
        For live models, will require labelers to provide a justification for their evaluation
        """
        self.definition.variants.incorrect_step.justification = False

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
