"""Edge classes for Project Workflows in Labelbox.

This module provides functionality for creating and managing edges (connections)
between workflow nodes, including edge factories and workflow references.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from labelbox.schema.workflow.enums import NodeOutput

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from labelbox.schema.workflow.base import BaseWorkflowNode

logger = logging.getLogger(__name__)


class WorkflowEdge(BaseModel):
    """Represents an edge (connection) in the workflow graph.

    An edge connects two nodes in the workflow, defining the flow of data
    from a source node to a target node through specific handles.

    Attributes:
        id: Unique identifier for the edge (format: xy-edge__{source}{sourceHandle}-{target}{targetHandle})
        source: ID of the source node
        target: ID of the target node
        sourceHandle: Output handle on the source node (e.g., 'if', 'else', 'approved', 'rejected')
        targetHandle: Input handle on the target node (typically 'in')

    Edge ID Format:
        Edge IDs follow the pattern: xy-edge__{source}{sourceHandle}-{target}{targetHandle}

        Example: xy-edge__node1if-node2in
        - Prefix: xy-edge__
        - Source node ID: node1
        - Source handle: if
        - Separator: -
        - Target node ID: node2
        - Target handle: in
    """

    id: str
    source: str
    target: str
    sourceHandle: str = Field(
        alias="sourceHandle",
        default="if",
        description="Output handle on source node (e.g., 'if', 'else', 'approved', 'rejected')",
    )
    targetHandle: str = Field(
        alias="targetHandle",
        default="in",
        description="Input handle on target node (typically 'in')",
    )

    # Reference to the workflow - will be set by the ProjectWorkflow class
    _workflow: Optional[Any] = PrivateAttr(
        default=None
    )  # Use Any to avoid circular imports

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    def get_source_node(self) -> Optional["BaseWorkflowNode"]:
        """Get the source node of this edge.

        Returns:
            The node that is the source of this edge, or None if not found
        """
        if self._workflow:
            return self._workflow.get_node_by_id(self.source)
        return None

    def get_target_node(self) -> Optional["BaseWorkflowNode"]:
        """Get the target node of this edge.

        Returns:
            The node that is the target of this edge, or None if not found
        """
        if self._workflow:
            return self._workflow.get_node_by_id(self.target)
        return None

    def set_workflow_reference(self, workflow: Any) -> None:
        """Set the workflow reference for this edge.

        Args:
            workflow: The workflow that contains this edge
        """
        self._workflow = workflow

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert the edge to a dictionary.

        Args:
            **kwargs: Additional parameters to pass to the parent model_dump method

        Returns:
            Dictionary representation of the edge
        """
        return super().model_dump(**kwargs)


class WorkflowEdgeFactory:
    """Factory class for creating workflow edges with proper validation.

    This factory handles edge creation, validation, and automatic updates
    to the workflow configuration.
    """

    def __init__(
        self, workflow: Any
    ) -> None:  # Use Any to avoid circular imports
        """Initialize the edge factory.

        Args:
            workflow: The workflow instance this factory will create edges for
        """
        self.workflow = workflow

    def create_edge(self, edge_data: Dict[str, Any]) -> WorkflowEdge:
        """Create a WorkflowEdge from edge data.

        Args:
            edge_data: Dictionary containing edge information

        Returns:
            The created edge object with workflow reference set
        """
        edge = WorkflowEdge(**edge_data)
        edge.set_workflow_reference(self.workflow)
        return edge

    def __call__(
        self,
        source: "BaseWorkflowNode",
        target: "BaseWorkflowNode",
        output_type: NodeOutput = NodeOutput.If,
    ) -> WorkflowEdge:
        """Create a workflow edge between two nodes.

        Creates a directed edge from the source node to the target node in the workflow.
        Handles validation, duplicate edge replacement, and special node configuration.

        Args:
            source: The source node of the edge
            target: The target node of the edge
            output_type: The type of output handle (e.g., If, Else, Approved, Rejected)

        Returns:
            The created workflow edge
        """
        # Ensure edges array exists in workflow config
        self._ensure_edges_array_exists()

        # Handle duplicate edge replacement
        source_handle = output_type.value
        self._handle_duplicate_edges(source, source_handle, target)

        # Create and configure the new edge
        edge = self._create_edge_instance(source, target, output_type)

        # Update workflow configuration
        self._update_workflow_config(edge)

        # Handle special node configurations (e.g., CustomReworkNode)
        self._handle_special_node_config(source)

        return edge

    def _ensure_edges_array_exists(self) -> None:
        """Ensure the edges array exists in the workflow config."""
        if "edges" not in self.workflow.config:
            logger.debug("Creating edges array in workflow config")
            self.workflow.config["edges"] = []

    def _handle_duplicate_edges(
        self,
        source: "BaseWorkflowNode",
        source_handle: str,
        target: "BaseWorkflowNode",
    ) -> None:
        """Handle replacement of existing edges from the same source handle.

        Args:
            source: Source node
            source_handle: Source handle being used
            target: Target node
        """
        # Check for existing edges with the same source and source handle
        for existing_edge in self.workflow.get_edges():
            if (
                existing_edge.source == source.id
                and existing_edge.sourceHandle == source_handle
            ):
                logger.warning(
                    f"Node {source.id} already has an outgoing connection from handle '{source_handle}'. "
                    f"Previous connection to {existing_edge.target} will be replaced with connection to {target.id}."
                )

                # Remove the existing edge from the config
                self.workflow.config["edges"] = [
                    edge
                    for edge in self.workflow.config["edges"]
                    if edge.get("id") != existing_edge.id
                ]

                # Clear edge cache to force rebuild
                self.workflow._edges_cache = None
                break

    def _create_edge_instance(
        self,
        source: "BaseWorkflowNode",
        target: "BaseWorkflowNode",
        output_type: NodeOutput,
    ) -> WorkflowEdge:
        """Create the WorkflowEdge instance.

        Args:
            source: Source node
            target: Target node
            output_type: Output type for the edge

        Returns:
            Created WorkflowEdge instance
        """
        # Generate edge ID using the correct format: xy-edge__{source}{sourceHandle}-{target}{targetHandle}
        source_handle = output_type.value
        target_handle = "in"
        edge_id = (
            f"xy-edge__{source.id}{source_handle}-{target.id}{target_handle}"
        )

        logger.debug(
            f"Creating edge {edge_id} from {source.id} to {target.id} with type {output_type.value}"
        )

        edge = WorkflowEdge(
            id=edge_id,
            source=source.id,
            target=target.id,
            sourceHandle=source_handle,
            targetHandle=target_handle,  # Explicitly set targetHandle
        )
        edge.set_workflow_reference(self.workflow)
        return edge

    def _update_workflow_config(self, edge: WorkflowEdge) -> None:
        """Update the workflow configuration with the new edge.

        Args:
            edge: The edge to add to the configuration
        """
        # Add to config and invalidate cache
        edge_data = edge.model_dump(
            by_alias=True
        )  # Use by_alias=True for proper serialization
        self.workflow.config["edges"].append(edge_data)

        # Update edge cache directly
        if self.workflow._edges_cache is not None:
            self.workflow._edges_cache.append(edge)
        else:
            # Initialize the cache with just this edge
            self.workflow._edges_cache = [edge]

        logger.debug(
            f"Added edge to config, now have {len(self.workflow.config['edges'])} edges"
        )

    def _handle_special_node_config(self, source: "BaseWorkflowNode") -> None:
        """Handle special configuration for specific node types.

        Currently handles CustomReworkNode custom_output flag setting.

        Args:
            source: The source node to check and configure
        """
        # Import at function level to avoid circular imports
        from labelbox.schema.workflow.enums import WorkflowDefinitionId

        # Check if source is a CustomReworkNode and set custom_output flag
        for node in self.workflow.config["nodes"]:
            if (
                node["id"] == source.id
                and node.get("definitionId")
                == WorkflowDefinitionId.CustomReworkTask.value
            ):
                self._set_custom_rework_output(node, source.id)
                break

    def _set_custom_rework_output(
        self, node: Dict[str, Any], node_id: str
    ) -> None:
        """Set the custom_output flag for CustomReworkNode.

        Args:
            node: Node configuration dictionary
            node_id: ID of the node for logging
        """
        # Initialize config array if it doesn't exist
        if "config" not in node:
            node["config"] = []

        # Check if custom_output is already in the config
        custom_output_exists = False
        for config_item in node.get("config", []):
            if config_item.get("field") == "custom_output":
                config_item["value"] = True
                custom_output_exists = True
                break

        # Add custom_output if not present
        if not custom_output_exists:
            node["config"].append(
                {
                    "field": "custom_output",
                    "value": True,
                    "metadata": None,
                }
            )

        # Reset nodes cache to ensure changes are reflected
        self.workflow._nodes_cache = None
        logger.debug(f"Set custom_output=True for CustomReworkNode {node_id}")
