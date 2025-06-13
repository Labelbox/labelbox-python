"""Terminal rework node for sending work back for corrections."""

import logging
from typing import Dict, List, Any, Optional, Literal
from pydantic import Field, field_validator

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
)

logger = logging.getLogger(__name__)

# Module-level constants
DEFAULT_FILTER_LOGIC_AND: Literal["and"] = "and"


class ReworkNode(BaseWorkflowNode):
    """
    Terminal rework node for sending work back for corrections.

    This node represents a terminal endpoint where work is sent back for rework.
    Unlike CustomReworkNode, this is a simple terminal node with no outputs that
    automatically routes work back to the initial rework entry point.

    Attributes:
        label (str): Display name for the node (default: "Rework")
        filter_logic (str): Logic for combining filters ("and" or "or", default: "and")
        definition_id (WorkflowDefinitionId): Node type identifier (read-only)
        output_if (None): If output (always None for terminal nodes)
        output_else (None): Else output (always None for terminal nodes)
        instructions (Optional[str]): Task instructions (read-only after creation)
        custom_fields (Dict[str, Any]): Additional custom configuration

    Inputs:
        Default: Must have exactly one input connection

    Outputs:
        None: Terminal node with no outputs (work flows back to InitialReworkNode)

    Validation:
        - Must have exactly one input connection
        - Cannot have any output connections
        - Instructions field is frozen after creation

    Usage Pattern:
        Used as a terminal node in workflows where work needs to be sent back
        for correction. Work automatically flows to InitialReworkNode for reassignment.

    Example:
        >>> rework = ReworkNode(
        ...     label="Send for Correction",
        ...     instructions="Work requires correction - see reviewer comments"
        ... )
        >>> # Connect from review node's rejected output
        >>> workflow.add_edge(review_node, rework, NodeOutput.Rejected)

    Note:
        This is a terminal node - work sent here automatically returns to the
        workflow's initial rework entry point without manual routing.
    """

    label: str = Field(default="Rework", max_length=50)
    filter_logic: Literal["and", "or"] = Field(
        default=DEFAULT_FILTER_LOGIC_AND, alias="filterLogic"
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.SendToRework,
        frozen=True,
        alias="definitionId",
    )
    # Only has one input, no outputs (data flows back to initial rework)
    output_if: None = Field(default=None, frozen=True)
    output_else: None = Field(default=None, frozen=True)
    instructions: Optional[str] = Field(
        default=None,
        description="Node instructions (stored as customFields.description in JSON)",
        frozen=True,  # Make instructions read-only
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v) -> List[str]:
        """Validate that rework node has exactly one input."""
        if len(v) != 1:
            raise ValueError("Rework node must have exactly one input")
        return v

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return []  # Terminal node, no outputs
