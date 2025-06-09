"""Review node for human quality control with approve/reject decisions."""

import logging
from typing import Dict, List, Any, Optional, Literal, Union
from pydantic import Field, field_validator, model_validator

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
)

logger = logging.getLogger(__name__)

# Module-level constants
DEFAULT_FILTER_LOGIC_OR: Literal["or"] = "or"


class ReviewNode(BaseWorkflowNode):
    """
    Review node for human quality control with approve/reject decisions.

    This node represents a human review step where reviewers can approve or reject
    work. It supports group assignments and has two outputs for routing approved
    and rejected work to different paths in the workflow.

    Attributes:
        label (str): Display name for the node (default: "Review task")
        filter_logic (str): Logic for combining filters ("and" or "or", default: "or")
        custom_fields (Dict[str, Any]): Additional custom configuration
        definition_id (WorkflowDefinitionId): Node type identifier (read-only)
        instructions (Optional[str]): Task instructions for reviewers
        group_assignment (Optional[Union[str, List[str], Any]]): User groups for assignment
        node_config (List[Dict[str, Any]]): API configuration for assignments

    Inputs:
        Default: Accepts exactly one input connection from previous workflow step

    Outputs:
        Approved: Route for work that passes review
        Rejected: Route for work that fails review and needs correction

    Assignment:
        - Supports user group assignment for distributed review
        - Accepts UserGroup objects, string IDs, or lists of IDs
        - Automatically syncs group assignments with API configuration
        - Multiple groups can be assigned for load balancing

    Validation:
        - Must have exactly one input connection
        - Both approved and rejected outputs can be connected
        - Group assignment is automatically converted to API format

    Example:
        >>> review = ReviewNode(
        ...     label="Quality Review",
        ...     group_assignment=["reviewer-group-id"],
        ...     instructions="Check annotation accuracy and completeness"
        ... )
        >>> # Connect inputs and outputs
        >>> workflow.add_edge(labeling_node, review)
        >>> workflow.add_edge(review, done_node, NodeOutput.Approved)
        >>> workflow.add_edge(review, rework_node, NodeOutput.Rejected)

    Note:
        Review nodes default to "or" filter logic, unlike most other nodes
        which default to "and" logic. This allows more flexible routing.
    """

    label: str = Field(default="Review task")
    # For ReviewNode, filter_logic defaults to "or"
    filter_logic: Literal["and", "or"] = Field(
        default=DEFAULT_FILTER_LOGIC_OR, alias="filterLogic"
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.ReviewTask,
        frozen=True,
        alias="definitionId",
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Node instructions (stored as customFields.description in JSON)",
    )
    group_assignment: Optional[Union[str, List[str], Any]] = Field(
        default=None,
        description="User group assignment for this review node. Can be a UserGroup object, a string ID, or a list of IDs.",
        alias="groupAssignment",
    )
    node_config: List[Dict[str, Any]] = Field(
        default_factory=lambda: [],
        description="Contains assignment rules etc.",
        alias="config",
    )

    @model_validator(mode="after")
    def sync_group_assignment_with_config(self) -> "ReviewNode":
        """Sync group_assignment with node_config for API compatibility."""
        if self.group_assignment is not None:
            group_ids = []

            # Handle different types of group assignment
            if hasattr(self.group_assignment, "uid"):
                # UserGroup object
                group_ids = [self.group_assignment.uid]
            elif isinstance(self.group_assignment, str):
                # Single string ID
                group_ids = [self.group_assignment]
            elif isinstance(self.group_assignment, list):
                # List of strings or UserGroup objects
                for item in self.group_assignment:
                    if hasattr(item, "uid"):
                        group_ids.append(item.uid)
                    elif isinstance(item, str):
                        group_ids.append(item)

            # Create config entries for group assignments
            if group_ids:
                # Update node_config with assignment rule in correct API format
                self.node_config = [
                    {
                        "field": "groupAssignment",
                        "value": group_ids,
                        "metadata": None,
                    }
                ]

        return self

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v) -> List[str]:
        """Validate that review node has exactly one input."""
        if len(v) != 1:
            raise ValueError("Review node must have exactly one input")
        return v

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return [NodeOutput.Approved, NodeOutput.Rejected]
