"""Initial rework node for rejected work requiring revision."""

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

# Type alias for config entries
ConfigEntry = Dict[str, Union[str, int, None]]


class InitialReworkNode(BaseWorkflowNode):
    """
    Initial rework node for rejected work requiring revision.

    This node serves as the entry point for data that has been rejected and needs
    to be reworked. It allows individual assignment to specific users and has one
    output that routes work back into the workflow for correction.

    Attributes:
        label (str): Display name for the node (read-only, default: "Rework (all rejected)")
        filter_logic (str): Logic for combining filters ("and" or "or", default: "and")
        definition_id (WorkflowDefinitionId): Node type identifier (read-only)
        inputs (List[str]): Input connections (always empty for initial nodes)
        output_else (None): Else output (always None for initial nodes)
        instructions (Optional[str]): Task instructions for rework
        custom_fields (Optional[Dict[str, Any]]): Additional custom configuration
        individual_assignment (Optional[Union[str, List[str]]]): User IDs for individual assignment
        node_config (List[ConfigEntry]): API configuration for assignments
        max_contributions_per_user (Optional[int]): Maximum contributions per user (null means infinite)

    Outputs:
        If: Single output connection for reworked items

    Assignment:
        - Supports individual user assignment via user IDs
        - Automatically syncs assignments with API configuration
        - Can assign to single user or first user from a list

    Validation:
        - Must have exactly one output_if connection
        - Cannot modify the node's name property
        - Label field is frozen after creation

    Example:
        >>> rework = InitialReworkNode(
        ...     individual_assignment=["specialist-user-id"],
        ...     instructions="Please review and correct the annotations",
        ...     max_contributions_per_user=5
        ... )
        >>> workflow.add_edge(rework, review_node)

    Note:
        This node automatically creates API configuration entries for user assignments
        to ensure proper routing in the Labelbox platform.
    """

    label: str = Field(
        default="Rework (all rejected)", frozen=True, max_length=50
    )
    filter_logic: Literal["and", "or"] = Field(
        default=DEFAULT_FILTER_LOGIC_AND, alias="filterLogic"
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.InitialReworkTask,
        frozen=True,
        alias="definitionId",
    )
    # Initial nodes don't have inputs - force to empty list and make it frozen
    inputs: List[str] = Field(default_factory=lambda: [], frozen=True)
    # Only has one output
    output_else: None = Field(default=None, frozen=True)
    instructions: Optional[str] = Field(
        default=None,
        description="Node instructions (stored as customFields.description in JSON)",
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {}, alias="customFields"
    )
    individual_assignment: Optional[Union[str, List[str]]] = Field(
        default_factory=lambda: [],
        description="List of user IDs for individual assignment or a single ID",
        alias="individualAssignment",
    )
    node_config: List[ConfigEntry] = Field(
        default_factory=lambda: [],
        description="Contains assignment rules etc.",
        alias="config",
    )
    max_contributions_per_user: Optional[int] = Field(
        default=None,
        description="Maximum contributions per user (null means infinite)",
        alias="maxContributionsPerUser",
        ge=0,
    )

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
    def sync_individual_assignment_with_config(self) -> "InitialReworkNode":
        """Sync individual_assignment and max_contributions_per_user with node_config for API compatibility."""
        # Start with existing config to preserve values that might have been set previously
        existing_config = getattr(self, "node_config", []) or []
        config_entries: List[ConfigEntry] = []

        # Preserve existing config entries first
        for entry in existing_config:
            if isinstance(entry, dict) and entry.get("field") in [
                "individualAssignment",
                "maxContributionsPerUser",
            ]:
                config_entries.append(entry)

        # Handle individual assignment only if it has a non-default value
        if self.individual_assignment and len(self.individual_assignment) > 0:
            # Handle both single string and list of strings
            if isinstance(self.individual_assignment, str):
                user_ids = [self.individual_assignment]
            else:
                user_ids = (
                    self.individual_assignment
                    if self.individual_assignment
                    else []
                )

            if user_ids:
                # Remove any existing individual assignment entries
                config_entries = [
                    e
                    for e in config_entries
                    if e.get("field") != "individualAssignment"
                ]

                # Use first user ID for assignment
                assignment_config: ConfigEntry = {
                    "field": "individualAssignment",
                    "value": user_ids[0],
                    "metadata": None,
                }
                config_entries.append(assignment_config)

        # Handle max contributions per user only if it has a non-None value
        if self.max_contributions_per_user is not None:
            # Remove any existing max contributions entries
            config_entries = [
                e
                for e in config_entries
                if e.get("field") != "maxContributionsPerUser"
            ]

            max_contributions_config: ConfigEntry = {
                "field": "maxContributionsPerUser",
                "value": self.max_contributions_per_user,
                "metadata": None,
            }
            config_entries.append(max_contributions_config)

        # Update node_config with all configuration entries
        self.node_config = config_entries

        # Sync changes back to workflow config
        self._sync_to_workflow()

        return self

    @field_validator("output_if")
    @classmethod
    def validate_output_if(cls, v) -> str:
        """Validate that output_if is not None."""
        if v is None:
            raise ValueError("Initial rework node must have an output")
        return v

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return [NodeOutput.Default]

    @property
    def name(self) -> Optional[str]:
        """Get the node's name (label)."""
        return self.raw_data.get("label")

    @name.setter
    def name(self, value: str) -> None:
        """Override name setter to prevent modification."""
        raise AttributeError(
            "Cannot modify name for InitialReworkNode, it is read-only"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """Custom setter to sync field changes with node_config."""
        super().__setattr__(name, value)

        # Only sync max_contributions_per_user changes after object is fully constructed
        # Don't interfere with individual_assignment - it has its own model_validator
        if (
            hasattr(self, "node_config")
            and hasattr(self, "id")  # Object is fully constructed
            and name == "max_contributions_per_user"
        ):
            self._sync_config()

    def _sync_config(self) -> None:
        """Sync field values with node_config."""
        # Start with existing individual assignment config if it exists
        config_entries: List[ConfigEntry] = []

        # Preserve existing individual assignment config entries
        for entry in getattr(self, "node_config", []):
            if entry.get("field") == "individualAssignment":
                config_entries.append(entry)

        # Handle max contributions per user
        if (
            hasattr(self, "max_contributions_per_user")
            and self.max_contributions_per_user is not None
        ):
            max_contributions_config: ConfigEntry = {
                "field": "maxContributionsPerUser",
                "value": self.max_contributions_per_user,
                "metadata": None,
            }
            config_entries.append(max_contributions_config)

        # Update node_config with all configuration entries
        if hasattr(self, "node_config"):
            self.node_config = config_entries

        # Sync changes back to workflow config
        self._sync_to_workflow()

    def _update_node_data(self, node_data: Dict[str, Any]) -> None:
        """Update individual node data in workflow config.

        Override base class to always update config field.
        """
        # Call parent implementation first
        super()._update_node_data(node_data)

        # Always update config field, even if empty (for max_contributions_per_user = None)
        node_data["config"] = getattr(self, "node_config", [])
