"""Base classes and mixins for Project Workflow nodes in Labelbox."""

import logging
from typing import Dict, List, Any, Optional, Tuple
from abc import abstractmethod
from pydantic import BaseModel, Field, ConfigDict

from labelbox.schema.workflow.enums import WorkflowDefinitionId, NodeOutput

logger = logging.getLogger(__name__)


def format_metadata_operator(operator: str) -> Tuple[str, str]:
    """Format metadata operator for display and JSON.

    Args:
        operator: Raw operator string

    Returns:
        Tuple of (display_operator, json_operator)

    Examples:
        >>> format_metadata_operator("contains")
        ('CONTAINS', 'contains')
        >>> format_metadata_operator("starts_with")
        ('STARTS WITH', 'starts_with')
    """
    operator_mappings = {
        "contains": ("CONTAINS", "contains"),
        "contain": ("CONTAINS", "contains"),
        "does_not_contain": ("DOES NOT CONTAIN", "does_not_contain"),
        "startswith": ("STARTS WITH", "starts_with"),
        "starts_with": ("STARTS WITH", "starts_with"),
        "start": ("STARTS WITH", "starts_with"),
        "endswith": ("ENDS WITH", "ends_with"),
        "ends_with": ("ENDS WITH", "ends_with"),
        "end": ("ENDS WITH", "ends_with"),
        "is_any": ("IS ANY", "is_any"),
        "is_not_any": ("IS NOT ANY", "is_not_any"),
    }

    return operator_mappings.get(operator, (operator.upper(), operator))


class NodePosition(BaseModel):
    """Represents the position of a node in the workflow canvas.

    Attributes:
        x: X coordinate position on the canvas
        y: Y coordinate position on the canvas
    """

    x: float = Field(default=0.0, description="X coordinate")
    y: float = Field(default=0.0, description="Y coordinate")


class InstructionsMixin:
    """Mixin to handle instructions syncing with custom_fields.description.

    This mixin ensures that instructions are properly synchronized between
    the node's instructions field and the customFields.description in the
    workflow configuration.
    """

    def sync_instructions_with_custom_fields(self) -> "InstructionsMixin":
        """Sync instructions with customFields.description.

        First attempts to load instructions from customFields.description if not set,
        then syncs instructions back to customFields if instructions is set.

        Returns:
            Self for method chaining
        """
        # Load instructions from customFields.description if not already set
        instructions = getattr(self, "instructions", None)
        custom_fields = getattr(self, "custom_fields", None)

        if (
            instructions is None
            and custom_fields
            and "description" in custom_fields
        ):
            # Use object.__setattr__ to bypass the frozen field restriction
            object.__setattr__(
                self, "instructions", custom_fields["description"]
            )

        # Sync instructions to customFields if instructions is set
        instructions = getattr(self, "instructions", None)
        if instructions is not None:
            custom_fields = getattr(self, "custom_fields", None)
            if custom_fields is None:
                object.__setattr__(self, "custom_fields", {})
                custom_fields = getattr(self, "custom_fields")
            custom_fields["description"] = instructions
        return self


class WorkflowSyncMixin:
    """Mixin to handle syncing node changes back to workflow config.

    This mixin provides functionality to keep the workflow configuration
    in sync when node properties are modified.
    """

    def _sync_to_workflow(self) -> None:
        """Sync node properties to the workflow config.

        Updates the workflow configuration with current node state including
        label, instructions, customFields, filters, and config.
        """
        workflow = getattr(self, "raw_data", {}).get("_workflow")
        if workflow and hasattr(workflow, "config"):
            node_id = getattr(self, "id", None)
            if not node_id:
                return

            for node_data in workflow.config.get("nodes", []):
                if node_data.get("id") == node_id:
                    self._update_node_data(node_data)
                    break

    def _update_node_data(self, node_data: Dict[str, Any]) -> None:
        """Update individual node data in workflow config.

        Args:
            node_data: Node data dictionary to update
        """
        # Update label
        if hasattr(self, "label"):
            node_data["label"] = getattr(self, "label")

        # Update instructions via customFields
        instructions = getattr(self, "instructions", None)
        if instructions is not None:
            if "customFields" not in node_data:
                node_data["customFields"] = {}
            node_data["customFields"]["description"] = instructions

        # Update customFields
        custom_fields = getattr(self, "custom_fields", None)
        if custom_fields:
            node_data["customFields"] = custom_fields

        # Update filters if present
        filters = getattr(self, "filters", None)
        if filters:
            node_data["filters"] = filters

        # Update config if present
        node_config = getattr(self, "node_config", None)
        if node_config:
            node_data["config"] = node_config

    def sync_property_change(self, property_name: str) -> None:
        """Handle property changes that need workflow syncing.

        Args:
            property_name: Name of the property that changed
        """
        if property_name == "instructions" and hasattr(self, "id"):
            # Also update custom_fields on the node object itself
            instructions = getattr(self, "instructions", None)
            if instructions is not None:
                custom_fields = getattr(self, "custom_fields", None)
                if custom_fields is None:
                    object.__setattr__(self, "custom_fields", {})
                    custom_fields = getattr(self, "custom_fields")
                custom_fields["description"] = instructions
            self._sync_to_workflow()


class BaseWorkflowNode(BaseModel, InstructionsMixin, WorkflowSyncMixin):
    """Base class for all workflow nodes with common functionality.

    Provides core node functionality including position management,
    input/output handling, and workflow synchronization.

    Attributes:
        id: Unique identifier for the node
        position: Node position on canvas
        definition_id: Type of workflow node
        inputs: List of input node IDs
        output_if: ID of node connected to 'if' output
        output_else: ID of node connected to 'else' output
        raw_data: Raw configuration data
    """

    id: str = Field(description="Unique identifier for the node")
    position: NodePosition = Field(
        default_factory=NodePosition, description="Node position on canvas"
    )
    definition_id: WorkflowDefinitionId = Field(
        alias="definitionId", description="Type of workflow node"
    )
    inputs: List[str] = Field(
        default_factory=list, description="List of input node IDs"
    )
    output_if: Optional[str] = Field(
        default=None, description="ID of node connected to 'if' output"
    )
    output_else: Optional[str] = Field(
        default=None, description="ID of node connected to 'else' output"
    )
    raw_data: Dict[str, Any] = Field(
        default_factory=dict, description="Raw configuration data"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    def __init__(self, **data):
        """Initialize the workflow node and sync instructions."""
        super().__init__(**data)
        # Sync instructions after initialization
        self.sync_instructions_with_custom_fields()

    @property
    @abstractmethod
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node.

        Must be implemented by subclasses to define which output types
        the node supports (e.g., If, Else, Default).
        """
        pass

    @property
    def name(self) -> Optional[str]:
        """Get the node's name (label).

        Returns:
            The node's display name or None if not set
        """
        return getattr(self, "label", None) or self.raw_data.get("label")

    @name.setter
    def name(self, value: str) -> None:
        """Set the node's name (updates label).

        Args:
            value: New name for the node
        """
        if hasattr(self, "label"):
            object.__setattr__(self, "label", value)
        self._sync_to_workflow()

    def __setattr__(self, name: str, value: Any) -> None:
        """Override setattr to handle workflow syncing for specific properties.

        Args:
            name: Property name
            value: Property value
        """
        super().__setattr__(name, value)
        if name == "instructions":
            self.sync_property_change(name)

    def __repr__(self) -> str:
        """Return a clean string representation of the node.

        Returns:
            String representation showing class name and node ID
        """
        return f"<{self.__class__.__name__} ID: {self.id}>"

    def __str__(self) -> str:
        """Return a clean string representation of the node.

        Returns:
            String representation showing class name and node ID
        """
        return f"<{self.__class__.__name__} ID: {self.id}>"
