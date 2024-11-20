from dataclasses import dataclass, field
from enum import Enum

from labelbox.schema.tool_building.base_step_reasoning_tool import (
    _BaseStepReasoningTool,
    _Definition,
    _Variant,
)
from labelbox.schema.tool_building.tool_type import ToolType


class IncorrectStepActions(Enum):
    REGENERATE_STEPS = "regenerateSteps"
    GENERATE_AND_RATE_ALTERNATIVE_STEPS = "generateAndRateAlternativeSteps"
    REWRITE_STEP = "rewriteStep"
    JUSTIFICATION = "justification"


def build_step_reasoning_definition():
    correct_step = _Variant(id=0, name="Correct", actions=[])
    neutral_step = _Variant(id=1, name="Neutral", actions=[])
    incorrect_step = _Variant(
        id=2,
        name="Incorrect",
        _available_actions={action.value for action in IncorrectStepActions},
        actions=[action.value for action in IncorrectStepActions],
    )
    variants = [correct_step, neutral_step, incorrect_step]
    return _Definition(variants=variants)


@dataclass
class StepReasoningTool(_BaseStepReasoningTool):
    """
    Use this class in OntologyBuilder to create a tool for step reasoning
    The definition field lists the possible options to evaulate a step

    NOTE: color attribute is for backward compatibility only and should not be set directly
    """

    type: ToolType = field(default=ToolType.STEP_REASONING, init=False)
    definition: _Definition = field(
        default_factory=build_step_reasoning_definition
    )

    def __post_init__(self):
        super().__post_init__()
        # Set available actions for variants 0, 1, 2 'out of band' since they are not passed in the definition
        self._set_variant_available_actions()

    def _set_variant_available_actions(self):
        for variant in self.definition.variants:
            if variant.id == 2:
                for action in IncorrectStepActions:
                    variant._available_actions.add(action.value)
