"""Initial labeling node for workflow entry point."""

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
DEFAULT_FILTER_LOGIC_AND: Literal["and"] = "and"

# Type alias for config entries
ConfigEntry = Dict[str, Union[str, int, None]]


class InitialLabelingNode(BaseWorkflowNode):
    """
    Initial labeling node representing the entry point for new labeling tasks.

    This node serves as the starting point for data that needs to be labeled for the
    first time. It has no inputs (as it's an entry point) and exactly one output that
    connects to the next step in the workflow. The node is immutable once created.

    Attributes:
        label (str): Display name for the node (read-only, default: "Initial labeling task")
        filter_logic (str): Logic for combining filters ("and" or "or", default: "and")
        definition_id (WorkflowDefinitionId): Node type identifier (read-only)
        inputs (List[str]): Input connections (always empty for initial nodes)
        output_else (None): Else output (always None for initial nodes)
        instructions (Optional[str]): Task instructions for labelers
        custom_fields (Dict[str, Any]): Additional custom configuration
        max_contributions_per_user (Optional[int]): Maximum contributions per user (null means infinite)
        node_config (List[ConfigEntry]): Contains configuration rules etc.

    Outputs:
        Default: Single output connection to next workflow step

    Validation:
        - Must have exactly one output_if connection
        - Cannot modify the node's name property
        - Label field is frozen after creation

    Example:
        >>> initial = InitialLabelingNode(
        ...     instructions="Please label all objects in the image",
        ...     max_contributions_per_user=10
        ... )
        >>> # Connect to next node
        >>> workflow.add_edge(initial, review_node)

    Note:
        This node type is automatically positioned as a workflow entry point
        and cannot have incoming connections from other nodes.
    """

    label: str = Field(
        default="Initial labeling task", frozen=True, max_length=50
    )
    filter_logic: Literal["and", "or"] = Field(
        default=DEFAULT_FILTER_LOGIC_AND, alias="filterLogic"
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.InitialLabelingTask,
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
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )
    max_contributions_per_user: Optional[int] = Field(
        default=None,
        description="Maximum contributions per user (null means infinite)",
        alias="maxContributionsPerUser",
        ge=0,
    )
    node_config: List[ConfigEntry] = Field(
        default_factory=lambda: [],
        description="Contains configuration rules etc.",
        alias="config",
    )

    @model_validator(mode="after")
    def sync_max_contributions_with_config(self) -> "InitialLabelingNode":
        """Sync max_contributions_per_user with node_config for API compatibility."""
        if self.max_contributions_per_user is not None:
            # Add max contributions config entry
            config_entry: ConfigEntry = {
                "field": "maxContributionsPerUser",
                "value": self.max_contributions_per_user,
                "metadata": None,
            }

            # Check if entry already exists and update it, otherwise add it
            updated = False
            for i, entry in enumerate(self.node_config):
                if entry.get("field") == "maxContributionsPerUser":
                    self.node_config[i] = config_entry
                    updated = True
                    break

            if not updated:
                self.node_config.append(config_entry)

        return self

    @field_validator("output_if")
    @classmethod
    def validate_output_if(cls, v) -> str:
        """Validate that output_if is not None."""
        if v is None:
            raise ValueError("Initial labeling node must have an output")
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
            "Cannot modify name for InitialLabelingNode, it is read-only"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """Custom setter to sync field changes with node_config."""
        super().__setattr__(name, value)

        # Sync changes to node_config when max_contributions_per_user is updated
        if name == "max_contributions_per_user" and hasattr(
            self, "node_config"
        ):
            self._sync_config()

    def _sync_config(self) -> None:
        """Sync max_contributions_per_user with node_config."""
        if (
            hasattr(self, "max_contributions_per_user")
            and self.max_contributions_per_user is not None
        ):
            # Add max contributions config entry
            config_entry: ConfigEntry = {
                "field": "maxContributionsPerUser",
                "value": self.max_contributions_per_user,
                "metadata": None,
            }

            # Check if entry already exists and update it, otherwise add it
            updated = False
            for i, entry in enumerate(self.node_config):
                if entry.get("field") == "maxContributionsPerUser":
                    self.node_config[i] = config_entry
                    updated = True
                    break

            if not updated:
                self.node_config.append(config_entry)
        else:
            # Remove the entry if value is None
            self.node_config = [
                entry
                for entry in self.node_config
                if entry.get("field") != "maxContributionsPerUser"
            ]

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
