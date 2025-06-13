"""Terminal completion node for finished work."""

import logging
from typing import Dict, List, Any, Optional
from pydantic import Field, field_validator

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
)

logger = logging.getLogger(__name__)


class DoneNode(BaseWorkflowNode):
    """
    Terminal completion node for finished work.

    This node represents a terminal endpoint where completed work is marked as done.
    It serves as the final destination for work that has successfully passed through
    all workflow steps and quality checks.

    Attributes:
        label (str): Display name for the node (default: "Done")
        definition_id (WorkflowDefinitionId): Node type identifier (read-only)
        output_if (None): If output (always None for terminal nodes)
        output_else (None): Else output (always None for terminal nodes)
        instructions (Optional[str]): Task instructions for completion
        custom_fields (Dict[str, Any]): Additional custom configuration

    Inputs:
        Default: Must have exactly one input connection

    Outputs:
        None: Terminal node with no outputs (work is marked complete)

    Validation:
        - Must have exactly one input connection
        - Cannot have any output connections
        - Serves as workflow completion endpoint

    Usage Pattern:
        Used as the final destination for successfully completed work.
        Multiple done nodes can exist for different completion paths.

    Example:
        >>> done = DoneNode(
        ...     label="Approved Work",
        ...     instructions="Work has been approved and is complete"
        ... )
        >>> # Connect from review node's approved output
        >>> workflow.add_edge(review_node, done, NodeOutput.Approved)

    Note:
        Work reaching a DoneNode is considered successfully completed
        and will not flow to any other nodes in the workflow.
    """

    label: str = Field(default="Done", max_length=50)
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.Done, frozen=True, alias="definitionId"
    )
    # Only has one input, no outputs (terminal node)
    output_if: None = Field(default=None, frozen=True)
    output_else: None = Field(default=None, frozen=True)
    instructions: Optional[str] = Field(
        default=None,
        description="Node instructions (stored as customFields.description in JSON)",
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v) -> List[str]:
        """Validate that done node has exactly one input."""
        if len(v) != 1:
            raise ValueError("Done node must have exactly one input")
        return v

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return []  # Terminal node, no outputs
