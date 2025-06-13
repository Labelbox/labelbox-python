"""Custom rework node with user/group assignments and single output."""

import logging
from typing import Dict, List, Any, Optional, Literal, Union
from pydantic import Field, field_validator, model_validator

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
    IndividualAssignment,
)

logger = logging.getLogger(__name__)

# Module-level constants
DEFAULT_FILTER_LOGIC_AND: Literal["and"] = "and"

# Type alias for config entries - use the same type as other nodes
ConfigEntry = Dict[str, Any]


class CustomReworkNode(BaseWorkflowNode):
    """
    Custom rework node with user/group assignments and single output.

    This node provides a customizable rework step that allows specific assignment
    to users or groups. Unlike the terminal ReworkNode, this node has one output
    that can connect to other workflow steps for continued processing.

    Attributes:
        label (str): Display name for the node (default: "")
        node_config (List[ConfigEntry]): API configuration for assignments
        filter_logic (str): Logic for combining filters ("and" or "or", default: "and")
        custom_fields (Dict[str, Any]): Additional custom configuration
        definition_id (WorkflowDefinitionId): Node type identifier (read-only)
        instructions (Optional[str]): Task instructions for rework
        group_assignment (Optional[Union[str, List[str], Any]]): User groups for assignment
        individual_assignment (Optional[Union[str, List[str]]]): User IDs for individual assignment
        max_contributions_per_user (Optional[int]): Maximum contributions per user (null means infinite)
        output_else (None): Else output (always None, only has if output)

    Inputs:
        Default: Must have exactly one input connection

    Outputs:
        If: Single output connection for reworked items to continue in workflow

    Assignment:
        - Supports both group and individual user assignment
        - Group assignment: Accepts UserGroup objects, string IDs, or lists of IDs
        - Individual assignment: Accepts single user ID or list of user IDs
        - Automatically syncs assignments with API configuration
        - Can combine both group and individual assignments

    Validation:
        - Must have exactly one input connection
        - Must have exactly one output_if connection
        - Assignment data is automatically converted to API format
        - Cannot have output_else connection

    Example:
        >>> custom_rework = CustomReworkNode(
        ...     label="Specialist Rework",
        ...     group_assignment=["specialist-group-id"],
        ...     individual_assignment=["expert-user-id"],
        ...     instructions="Please review and correct annotation accuracy",
        ...     max_contributions_per_user=3
        ... )
        >>> # Connect to continue workflow after rework
        >>> workflow.add_edge(review_node, custom_rework, NodeOutput.Rejected)
        >>> workflow.add_edge(custom_rework, final_review, NodeOutput.If)

    Assignment Priority:
        When both group and individual assignments are specified, the system
        will use both assignment types as configured in the API format.

    Note:
        Unlike ReworkNode (terminal), CustomReworkNode allows work to continue
        through the workflow after rework is completed, enabling multi-stage
        rework processes and quality checks.
    """

    label: str = Field(default="", max_length=50)
    node_config: List[ConfigEntry] = Field(
        default_factory=lambda: [],
        description="Contains assignment rules etc.",
        alias="config",
    )
    filter_logic: Literal["and", "or"] = Field(
        default=DEFAULT_FILTER_LOGIC_AND, alias="filterLogic"
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.CustomReworkTask,
        frozen=True,
        alias="definitionId",
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Node instructions (stored as customFields.description in JSON)",
    )
    group_assignment: Optional[Union[str, List[str], Any]] = Field(
        default=None,
        description="User group assignment for this rework node. Can be a UserGroup object, a string ID, or a list of IDs.",
        alias="groupAssignment",
    )
    individual_assignment: Optional[Union[str, List[str]]] = Field(
        default_factory=lambda: [],
        description="List of user IDs for individual assignment or a single ID",
        alias="individualAssignment",
    )
    max_contributions_per_user: Optional[int] = Field(
        default=None,
        description="Maximum contributions per user (null means infinite)",
        alias="maxContributionsPerUser",
        ge=0,
    )
    # Has one input and one output
    output_else: None = Field(default=None, frozen=True)  # Only one output (if)

    @field_validator("individual_assignment", mode="before")
    @classmethod
    def convert_individual_assignment(cls, v):
        """Convert IndividualAssignment enum values to strings before validation."""
        if v is None:
            return v

        # Handle single enum value
        if hasattr(v, "value") and isinstance(v, IndividualAssignment):
            return v.value

        # Handle list containing enum values
        if isinstance(v, list):
            converted = []
            for item in v:
                if hasattr(item, "value") and isinstance(
                    item, IndividualAssignment
                ):
                    converted.append(item.value)
                else:
                    converted.append(item)
            return converted

        return v

    @model_validator(mode="after")
    def sync_assignments_with_config(self) -> "CustomReworkNode":
        """Sync group_assignment, individual_assignment, and max_contributions_per_user with node_config for API compatibility."""
        config_items = []

        # Handle group assignment
        if self.group_assignment is not None:
            # Extract user group IDs from UserGroup objects if needed
            if hasattr(self.group_assignment, "__iter__") and not isinstance(
                self.group_assignment, str
            ):
                # It's a list of UserGroup objects or IDs
                group_ids = []
                for item in self.group_assignment:
                    if hasattr(item, "uid"):
                        # It's a UserGroup object
                        group_ids.append(item.uid)
                    else:
                        # It's already an ID string
                        group_ids.append(str(item))
            elif hasattr(self.group_assignment, "uid"):
                # Single UserGroup object
                group_ids = [self.group_assignment.uid]
            else:
                # Single ID string
                group_ids = [str(self.group_assignment)]

            config_items.append(
                {
                    "field": "groupAssignment",
                    "value": group_ids,
                    "metadata": None,
                }
            )

        # Handle individual assignment
        if self.individual_assignment:
            # Handle both single ID and list of IDs
            if (
                isinstance(self.individual_assignment, list)
                and len(self.individual_assignment) > 0
            ):
                # Use first ID if it's a list
                assignment_value = (
                    self.individual_assignment[0]
                    if isinstance(self.individual_assignment[0], str)
                    else str(self.individual_assignment[0])
                )
            elif isinstance(self.individual_assignment, str):
                assignment_value = self.individual_assignment
            else:
                assignment_value = str(self.individual_assignment)

            config_items.append(
                {
                    "field": "individualAssignment",
                    "value": assignment_value,
                    "metadata": None,
                }
            )

        # Handle max contributions per user
        if self.max_contributions_per_user is not None:
            max_contributions_config: ConfigEntry = {
                "field": "maxContributionsPerUser",
                "value": self.max_contributions_per_user,
                "metadata": None,
            }
            config_items.append(max_contributions_config)

        # Add any existing config items that aren't assignments or max contributions
        existing_config = getattr(self, "node_config", []) or []
        for item in existing_config:
            if isinstance(item, dict) and item.get("field") not in [
                "groupAssignment",
                "individualAssignment",
                "maxContributionsPerUser",
            ]:
                config_items.append(item)

        self.node_config = config_items
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        """Custom setter to sync field changes with node_config."""
        super().__setattr__(name, value)

        # Only sync after object is fully constructed and for relevant fields
        if (
            hasattr(self, "node_config")
            and hasattr(self, "id")  # Object is fully constructed
            and name
            in (
                "max_contributions_per_user",
                "group_assignment",
                "individual_assignment",
            )
        ):
            self._sync_config()

    def _sync_config(self) -> None:
        """Sync field values with node_config."""
        config_items = []

        # Handle group assignment - properly check for None
        group_assignment = getattr(self, "group_assignment", None)
        if group_assignment is not None:
            # Extract user group IDs from UserGroup objects if needed
            if hasattr(group_assignment, "__iter__") and not isinstance(
                group_assignment, str
            ):
                # It's a list of UserGroup objects or IDs
                group_ids = []
                for item in group_assignment:
                    if hasattr(item, "uid"):
                        # It's a UserGroup object
                        group_ids.append(item.uid)
                    else:
                        # It's already an ID string
                        group_ids.append(str(item))
            elif hasattr(group_assignment, "uid"):
                # Single UserGroup object
                group_ids = [group_assignment.uid]
            else:
                # Single ID string
                group_ids = [str(group_assignment)]

            config_items.append(
                {
                    "field": "groupAssignment",
                    "value": group_ids,
                    "metadata": None,
                }
            )

        # Handle individual assignment
        individual_assignment = getattr(self, "individual_assignment", None)
        if individual_assignment:
            # Handle both single ID and list of IDs
            if (
                isinstance(individual_assignment, list)
                and len(individual_assignment) > 0
            ):
                # Use first ID if it's a list
                assignment_value = (
                    individual_assignment[0]
                    if isinstance(individual_assignment[0], str)
                    else str(individual_assignment[0])
                )
            elif isinstance(individual_assignment, str):
                assignment_value = individual_assignment
            else:
                assignment_value = str(individual_assignment)

            config_items.append(
                {
                    "field": "individualAssignment",
                    "value": assignment_value,
                    "metadata": None,
                }
            )

        # Handle max contributions per user
        max_contributions = getattr(self, "max_contributions_per_user", None)
        if max_contributions is not None:
            max_contributions_config: ConfigEntry = {
                "field": "maxContributionsPerUser",
                "value": max_contributions,
                "metadata": None,
            }
            config_items.append(max_contributions_config)

        # Preserve existing config items that aren't assignments or max contributions
        for item in getattr(self, "node_config", []):
            if isinstance(item, dict) and item.get("field") not in [
                "groupAssignment",
                "individualAssignment",
                "maxContributionsPerUser",
            ]:
                config_items.append(item)

        # Update node_config
        if hasattr(self, "node_config"):
            self.node_config = config_items

        # Sync changes back to workflow config
        self._sync_to_workflow()

    def _update_node_data(self, node_data: Dict[str, Any]) -> None:
        """Update individual node data in workflow config.

        Override base class to always update config field.
        """
        # Call parent implementation first
        super()._update_node_data(node_data)

        # Always update config field, even if empty
        node_data["config"] = getattr(self, "node_config", [])

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v) -> List[str]:
        """Validate that custom rework node has exactly one input."""
        if len(v) != 1:
            raise ValueError("Custom rework node must have exactly one input")
        return v

    @field_validator("output_if")
    @classmethod
    def validate_output_if(cls, v) -> str:
        """Validate that output_if is not None."""
        if v is None:
            raise ValueError("Custom rework node must have an output_if")
        return v

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return [NodeOutput.If]  # Only one output
