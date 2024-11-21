from dataclasses import dataclass, field
from enum import Enum

from labelbox.schema.tool_building.base_step_reasoning_tool import (
    _BaseStepReasoningTool,
    _Definition,
    _Variant,
)
from labelbox.schema.tool_building.tool_type import ToolType


class FactCheckingActions(Enum):
    WRITE_JUSTIFICATION = "justification"


def build_fact_checking_definition():
    accurate_step = _Variant(
        id=0,
        name="Accurate",
        _available_actions={action.value for action in FactCheckingActions},
        actions=[action.value for action in FactCheckingActions],
    )
    inaccurate_step = _Variant(
        id=1,
        name="Inaccurate",
        _available_actions={action.value for action in FactCheckingActions},
        actions=[action.value for action in FactCheckingActions],
    )
    disputed_step = _Variant(
        id=2,
        name="Disputed",
        _available_actions={action.value for action in FactCheckingActions},
        actions=[action.value for action in FactCheckingActions],
    )
    unsupported_step = _Variant(
        id=3,
        name="Unsupported",
        _available_actions=set(),
        actions=[],
    )
    cant_confidently_assess_step = _Variant(
        id=4,
        name="Can't confidently assess",
        _available_actions=set(),
        actions=[],
    )
    no_factual_information_step = _Variant(
        id=5,
        name="No factual information",
        _available_actions=set(),
        actions=[],
    )
    variants = [
        accurate_step,
        inaccurate_step,
        disputed_step,
        unsupported_step,
        cant_confidently_assess_step,
        no_factual_information_step,
    ]
    return _Definition(variants=variants)


@dataclass
class FactCheckingTool(_BaseStepReasoningTool):
    """
    Use this class in OntologyBuilder to create a tool for fact checking

    Note variant kinds can not be changed
    """

    type: ToolType = field(default=ToolType.FACT_CHECKING, init=False)
    definition: _Definition = field(
        default_factory=build_fact_checking_definition
    )

    def __post_init__(self):
        super().__post_init__()
        # Set available actions for variants 0, 1, 2 'out of band' since they are not passed in the definition
        self._set_variant_available_actions()

    def _set_variant_available_actions(self):
        for variant in self.definition.variants:
            if variant.id in [0, 1, 2]:
                for action in FactCheckingActions:
                    variant._available_actions.add(action.value)
