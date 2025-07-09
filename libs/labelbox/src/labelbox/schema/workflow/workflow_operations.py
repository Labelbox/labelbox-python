"""
Workflow operations for node creation and workflow manipulation.

This module contains operation classes that create and manipulate workflow
structure, including node creation factory and workflow operations.
"""

import logging
import uuid
from datetime import datetime
from typing import (
    Dict,
    List,
    Any,
    Optional,
    Type,
    cast,
    Union,
    Literal,
    overload,
    TYPE_CHECKING,
)

from labelbox.schema.workflow.base import BaseWorkflowNode, NodePosition
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeType,
    MatchFilters,
    Scope,
)
from labelbox.schema.workflow.nodes import (
    InitialLabelingNode,
    InitialReworkNode,
    ReviewNode,
    ReworkNode,
    DoneNode,
    CustomReworkNode,
    LogicNode,
    AutoQANode,
)
from labelbox.schema.workflow.project_filter import ProjectWorkflowFilter

if TYPE_CHECKING:
    from labelbox.schema.workflow.workflow import ProjectWorkflow

logger = logging.getLogger(__name__)

# Mapping from definitionId Enum to Node Class
NODE_TYPE_MAP = {
    WorkflowDefinitionId.InitialLabelingTask: InitialLabelingNode,
    WorkflowDefinitionId.InitialReworkTask: InitialReworkNode,
    WorkflowDefinitionId.ReviewTask: ReviewNode,
    WorkflowDefinitionId.SendToRework: ReworkNode,
    WorkflowDefinitionId.Logic: LogicNode,
    WorkflowDefinitionId.Done: DoneNode,
    WorkflowDefinitionId.CustomReworkTask: CustomReworkNode,
    WorkflowDefinitionId.AutoQA: AutoQANode,
}


def _get_definition_id_for_class(
    NodeClass: Type[BaseWorkflowNode],
) -> WorkflowDefinitionId:
    """Get the appropriate WorkflowDefinitionId for a given node class."""
    # Check the NODE_TYPE_MAP first for direct mapping
    for enum_val, mapped_class in NODE_TYPE_MAP.items():
        if mapped_class == NodeClass:
            return enum_val

    # Fallback based on class inheritance
    class_mapping = {
        InitialLabelingNode: WorkflowDefinitionId.InitialLabelingTask,
        InitialReworkNode: WorkflowDefinitionId.InitialReworkTask,
        ReviewNode: WorkflowDefinitionId.ReviewTask,
        ReworkNode: WorkflowDefinitionId.SendToRework,
        LogicNode: WorkflowDefinitionId.Logic,
        DoneNode: WorkflowDefinitionId.Done,
        CustomReworkNode: WorkflowDefinitionId.CustomReworkTask,
        AutoQANode: WorkflowDefinitionId.AutoQA,
    }

    for base_class, definition_id in class_mapping.items():
        if issubclass(NodeClass, base_class):
            return definition_id

    # Last resort fallback
    logger.warning(
        f"Could not determine definitionId for {NodeClass.__name__}. "
        f"Using InitialLabelingTask as default."
    )
    return WorkflowDefinitionId.InitialLabelingTask


class WorkflowNodeFactory:
    """Factory for creating workflow nodes with proper validation and configuration."""

    @staticmethod
    def get_node_position(
        workflow: "ProjectWorkflow",
        after_node_id: Optional[str] = None,
        default_x: float = 0,
        default_y: float = 0,
    ) -> NodePosition:
        """Get the position for a new node."""
        if after_node_id:
            after_node = workflow.get_node_by_id(after_node_id)
            if after_node:
                return NodePosition(
                    x=after_node.position.x + 250,
                    y=after_node.position.y,
                )
        return NodePosition(x=default_x, y=default_y)

    @staticmethod
    def create_node_internal(
        workflow: "ProjectWorkflow",
        NodeClass: Type[BaseWorkflowNode],
        x: Optional[float] = None,
        y: Optional[float] = None,
        after_node_id: Optional[str] = None,
        **kwargs,
    ) -> BaseWorkflowNode:
        """Internal method to create a node with proper position and ID."""
        # Generate a unique ID if not provided
        node_id = kwargs.pop("id", f"{uuid.uuid4()}")

        # Convert 'name' to 'label' if present for all nodes that support it
        if "name" in kwargs and "label" not in kwargs:
            kwargs["label"] = kwargs.pop("name")

        # Get position
        position = WorkflowNodeFactory.get_node_position(
            workflow, after_node_id, x or 0, y or 0
        )

        # Determine the appropriate definition_id if not provided
        definition_id = kwargs.pop("definition_id", None)
        if definition_id is None:
            definition_id = _get_definition_id_for_class(NodeClass)

        # Prepare constructor arguments with all required fields
        raw_data = kwargs.copy()
        # Store the workflow reference in raw_data for syncing
        raw_data["_workflow"] = workflow

        constructor_args = {
            "id": node_id,
            "position": position,
            "definitionId": definition_id,
            "raw_data": raw_data,
        }
        constructor_args.update(kwargs)

        # Create the node with all parameters
        node = NodeClass(**constructor_args)

        # Ensure we have a valid definition_id value (not Unknown)
        if node.definition_id == WorkflowDefinitionId.Unknown:
            logger.warning(
                f"Node {node.id} has Unknown definition_id. "
                f"Setting to InitialLabelingTask to prevent API errors."
            )
            # Set fallback value since definition_id is immutable after creation
            # We modify the underlying raw_data to ensure API compatibility
            node.raw_data["definitionId"] = (
                WorkflowDefinitionId.InitialLabelingTask.value
            )

        # Prepare node data for config
        node_data = {
            "id": node.id,
            "position": node.position.model_dump(),
            "definitionId": (
                WorkflowDefinitionId.InitialLabelingTask.value
                if node.definition_id == WorkflowDefinitionId.Unknown
                else node.definition_id.value
            ),
        }

        # Add label if present (this handles the 'name' parameter)
        if hasattr(node, "label") and node.label:
            node_data["label"] = node.label

        # Handle instructions - store in customFields for API and sync with node
        if hasattr(node, "instructions") and node.instructions is not None:
            # Ensure custom_fields exists in raw_data
            if "customFields" not in node.raw_data:
                node.raw_data["customFields"] = {}

            # Sync instructions to customFields.description
            node.raw_data["customFields"]["description"] = node.instructions

        # Add filterLogic if present
        if hasattr(node, "filter_logic") and node.filter_logic:
            node_data["filterLogic"] = node.filter_logic

        # Add customFields if present (merge with instructions if both exist)
        if hasattr(node, "custom_fields") and node.custom_fields:
            if "customFields" not in node_data:
                node_data["customFields"] = {}
            # Ensure customFields is a dict before updating
            if isinstance(node_data["customFields"], dict):
                node_data["customFields"].update(node.custom_fields)

        # Add config if present
        if hasattr(node, "node_config") and node.node_config:
            node_data["config"] = node.node_config

        # Add filters if present
        if hasattr(node, "filters") and node.filters:
            node_data["filters"] = node.filters

        # Add inputs if present
        if hasattr(node, "inputs") and node.inputs:
            node_data["inputs"] = node.inputs

        # Add to config
        workflow.config["nodes"].append(node_data)

        # Reset the nodes cache to ensure it's up-to-date
        workflow._nodes_cache = None

        return node

    # Overloaded add_node methods for type safety

    @staticmethod
    @overload
    def add_node(
        workflow: "ProjectWorkflow",
        *,
        type: Literal[NodeType.Review],
        name: str = "Review task",
        instructions: Optional[str] = None,
        group_assignment: Optional[Union[str, List[str], Any]] = None,
        max_contributions_per_user: Optional[int] = None,
        **kwargs: Any,
    ) -> ReviewNode: ...

    @staticmethod
    @overload
    def add_node(
        workflow: "ProjectWorkflow",
        *,
        type: Literal[NodeType.Rework],
        name: str = "Rework",
        **kwargs: Any,
    ) -> ReworkNode: ...

    @staticmethod
    @overload
    def add_node(
        workflow: "ProjectWorkflow",
        *,
        type: Literal[NodeType.Logic],
        name: str = "Logic",
        filters: Optional[
            Union[List[Dict[str, Any]], ProjectWorkflowFilter]
        ] = None,
        match_filters: MatchFilters = MatchFilters.All,
        **kwargs: Any,
    ) -> LogicNode: ...

    @staticmethod
    @overload
    def add_node(
        workflow: "ProjectWorkflow",
        *,
        type: Literal[NodeType.Done],
        name: str = "Done",
        **kwargs: Any,
    ) -> DoneNode: ...

    @staticmethod
    @overload
    def add_node(
        workflow: "ProjectWorkflow",
        *,
        type: Literal[NodeType.CustomRework],
        name: str = "",
        instructions: Optional[str] = None,
        group_assignment: Optional[Union[str, List[str], Any]] = None,
        individual_assignment: Optional[Union[str, List[str]]] = None,
        max_contributions_per_user: Optional[int] = None,
        **kwargs: Any,
    ) -> CustomReworkNode: ...

    @staticmethod
    @overload
    def add_node(
        workflow: "ProjectWorkflow",
        *,
        type: Literal[NodeType.AutoQA],
        name: str = "Label Score (AutoQA)",
        evaluator_id: str,
        scope: Scope = Scope.All,
        score_name: str,
        score_threshold: float,
        **kwargs: Any,
    ) -> AutoQANode: ...

    @staticmethod
    @overload
    def add_node(
        workflow: "ProjectWorkflow", *, type: NodeType, **kwargs: Any
    ) -> BaseWorkflowNode: ...

    @staticmethod
    def add_node(
        workflow: "ProjectWorkflow", *, type: NodeType, **kwargs: Any
    ) -> BaseWorkflowNode:
        """Add a node to the workflow with type-specific parameters."""
        # Get the node class from the type
        workflow_def_id = WorkflowDefinitionId(type.value)
        node_class = NODE_TYPE_MAP[workflow_def_id]

        # Handle special parameter transformations
        processed_kwargs = kwargs.copy()

        # Convert 'name' to 'label' for consistency
        if "name" in processed_kwargs:
            processed_kwargs["label"] = processed_kwargs.pop("name")

        # Handle LogicNode match_filters -> filter_logic conversion
        if type == NodeType.Logic and "match_filters" in processed_kwargs:
            match_filters_value = processed_kwargs.pop("match_filters")
            # Map MatchFilters enum to server-expected values
            if match_filters_value == MatchFilters.Any:
                processed_kwargs["filter_logic"] = (
                    "or"  # Server expects "or" for Any
                )
            else:  # MatchFilters.All
                processed_kwargs["filter_logic"] = (
                    "and"  # Server expects "and" for All
                )

        # Handle LogicNode filters conversion from ProjectWorkflowFilter to list
        if type == NodeType.Logic and "filters" in processed_kwargs:
            filters_value = processed_kwargs["filters"]
            if hasattr(filters_value, "to_dict") and callable(
                filters_value.to_dict
            ):
                try:
                    # Convert ProjectWorkflowFilter to list of dictionaries
                    processed_kwargs["filters"] = filters_value.to_dict()
                except Exception:
                    # If to_dict() fails, try to access filters attribute directly
                    if hasattr(filters_value, "filters") and isinstance(
                        filters_value.filters, list
                    ):
                        processed_kwargs["filters"] = filters_value.filters

        # Handle AutoQA scope parameter
        if type == NodeType.AutoQA and "scope" in processed_kwargs:
            scope_value = processed_kwargs["scope"]
            processed_kwargs["scope"] = (
                scope_value.value
                if isinstance(scope_value, Scope)
                else scope_value
            )

        # Handle CustomRework custom_output parameter
        if (
            type == NodeType.CustomRework
            and "custom_output" in processed_kwargs
        ):
            # This will be handled by the node's model validator
            pass

        # Remove custom_fields and filter_logic if user tries to set them directly
        # These are managed internally and should not be set by users
        processed_kwargs.pop("custom_fields", None)
        if type != NodeType.Logic:  # LogicNode filter_logic is handled above
            processed_kwargs.pop("filter_logic", None)

        # Use the existing internal method to create the node
        return WorkflowNodeFactory.create_node_internal(
            workflow,
            cast(Type[BaseWorkflowNode], node_class),
            **processed_kwargs,
        )


class WorkflowOperations:
    """Operations for manipulating workflow structure and content."""

    @staticmethod
    def copy_workflow_structure(
        source_workflow: "ProjectWorkflow",
        target_client,
        target_project_id: str,
    ) -> "ProjectWorkflow":
        """Copy the workflow structure from a source workflow to a new project.

        IMPORTANT: This method preserves existing initial node IDs in the target workflow
        to prevent workflow breakage. Only non-initial nodes get new IDs.
        """
        try:
            # Create a new workflow in the target project
            from labelbox.schema.workflow.workflow import ProjectWorkflow

            target_workflow = ProjectWorkflow.get_workflow(
                target_client, target_project_id
            )

            # Find existing initial nodes in target workflow to preserve their IDs
            existing_initial_ids = {}
            for node_data in target_workflow.config.get("nodes", []):
                definition_id = node_data.get("definitionId")
                if (
                    definition_id
                    == WorkflowDefinitionId.InitialLabelingTask.value
                ):
                    existing_initial_ids[
                        WorkflowDefinitionId.InitialLabelingTask.value
                    ] = node_data.get("id")
                elif (
                    definition_id
                    == WorkflowDefinitionId.InitialReworkTask.value
                ):
                    existing_initial_ids[
                        WorkflowDefinitionId.InitialReworkTask.value
                    ] = node_data.get("id")

            # Get the source config
            new_config = source_workflow.config.copy()
            old_to_new_id_map = {}

            # Generate new IDs for all nodes, but preserve existing initial node IDs
            if new_config.get("nodes"):
                updated_nodes = []
                for node in new_config["nodes"]:
                    definition_id = node.get("definitionId")
                    old_id = node["id"]

                    # Preserve existing initial node IDs, generate new IDs for others
                    if definition_id in existing_initial_ids:
                        new_id = existing_initial_ids[definition_id]
                    else:
                        new_id = str(uuid.uuid4())

                    old_to_new_id_map[old_id] = new_id
                    updated_nodes.append(
                        {
                            **node,
                            "id": new_id,
                        }
                    )

                new_config["nodes"] = updated_nodes

            # Update edges to use the new node IDs
            if new_config.get("edges"):
                updated_edges = []
                for edge in new_config["edges"]:
                    source_id = old_to_new_id_map[edge["source"]]
                    target_id = old_to_new_id_map[edge["target"]]
                    source_handle = edge.get("sourceHandle", "if")
                    target_handle = edge.get("targetHandle", "in")

                    # Generate edge ID using correct format: xy-edge__{source}{sourceHandle}-{target}{targetHandle}
                    edge_id = f"xy-edge__{source_id}{source_handle}-{target_id}{target_handle}"

                    updated_edges.append(
                        {
                            **edge,
                            "id": edge_id,
                            "source": source_id,
                            "target": target_id,
                        }
                    )

                new_config["edges"] = updated_edges

            # Update the target workflow with the new config
            target_workflow.config = new_config

            # Save the changes
            target_workflow.update_config()

            return target_workflow

        except Exception as e:
            logger.error(f"Error copying workflow: {e}")
            raise ValueError(f"Could not copy workflow structure: {e}")

    @staticmethod
    def copy_from(
        workflow: "ProjectWorkflow",
        source_workflow: "ProjectWorkflow",
        auto_layout: bool = True,
    ) -> "ProjectWorkflow":
        """Copy the nodes and edges from a source workflow to this workflow.

        IMPORTANT: This method preserves existing initial node IDs in the target workflow
        to prevent workflow breakage. Only non-initial nodes get new IDs.
        """
        try:
            # Find existing initial nodes in target workflow to preserve their IDs
            existing_initial_ids = {}
            for node_data in workflow.config.get("nodes", []):
                definition_id = node_data.get("definitionId")
                if (
                    definition_id
                    == WorkflowDefinitionId.InitialLabelingTask.value
                ):
                    existing_initial_ids[
                        WorkflowDefinitionId.InitialLabelingTask.value
                    ] = node_data.get("id")
                elif (
                    definition_id
                    == WorkflowDefinitionId.InitialReworkTask.value
                ):
                    existing_initial_ids[
                        WorkflowDefinitionId.InitialReworkTask.value
                    ] = node_data.get("id")

            # Create a clean work config (without connections)
            work_config: Dict[str, List[Any]] = {"nodes": [], "edges": []}

            # Create temporary working config to track connections
            temp_config: Dict[str, List[Any]] = {"nodes": [], "edges": []}

            # Create a mapping of old node IDs to new node IDs
            id_mapping: Dict[str, str] = {}

            # First pass: Create all nodes by directly copying configuration
            for source_node_data in source_workflow.config.get("nodes", []):
                definition_id = source_node_data.get("definitionId")
                old_id = source_node_data.get("id")

                # Preserve existing initial node IDs, generate new IDs for others
                if definition_id in existing_initial_ids:
                    new_id = existing_initial_ids[definition_id]
                else:
                    new_id = f"node-{uuid.uuid4()}"

                id_mapping[old_id] = new_id

                # Create a new node data dictionary by copying the source node
                new_node_data = source_node_data.copy()

                # Update the ID and reset connections that we'll recreate later
                new_node_data["id"] = new_id

                # Set tracking info in our temp config
                temp_node = new_node_data.copy()
                temp_node["inputs"] = []
                temp_node["output_if"] = None
                temp_node["output_else"] = None
                temp_config["nodes"].append(temp_node)

                # Create clean node for the actual API (without connection fields)
                api_node = new_node_data.copy()
                api_node.pop("inputs", None)
                api_node.pop("output_if", None)
                api_node.pop("output_else", None)
                work_config["nodes"].append(api_node)

            # Second pass: Create all edges
            for source_edge_data in source_workflow.config.get("edges", []):
                source_id = source_edge_data.get("source")
                target_id = source_edge_data.get("target")

                # Skip edges for nodes that weren't copied
                if source_id not in id_mapping or target_id not in id_mapping:
                    continue

                # Create new edge
                source_handle = source_edge_data.get("sourceHandle", "out")
                target_handle = source_edge_data.get("targetHandle", "in")

                # Generate edge ID using correct format: xy-edge__{source}{sourceHandle}-{target}{targetHandle}
                edge_id = f"xy-edge__{id_mapping[source_id]}{source_handle}-{id_mapping[target_id]}{target_handle}"

                new_edge = {
                    "id": edge_id,
                    "source": id_mapping[source_id],
                    "target": id_mapping[target_id],
                    "sourceHandle": source_handle,
                    "targetHandle": target_handle,
                }

                # Add the edge to config
                work_config["edges"].append(new_edge)
                temp_config["edges"].append(new_edge)

                # Update node connections in temp config
                # Find target node and add input
                for node in temp_config["nodes"]:
                    if node["id"] == id_mapping[target_id]:
                        node["inputs"].append(id_mapping[source_id])

                # Find source node and set output
                for node in temp_config["nodes"]:
                    if node["id"] == id_mapping[source_id]:
                        # Set output based on sourceHandle
                        source_handle = source_edge_data.get("sourceHandle", "")
                        if source_handle in ("if", "approved", "out"):
                            node["output_if"] = id_mapping[target_id]
                        elif source_handle in ("else", "rejected"):
                            node["output_else"] = id_mapping[target_id]

            # For internal state tracking - we keep the full config with connections
            workflow.config = temp_config

            # Reset caches
            workflow._nodes_cache = None
            workflow._edges_cache = None

            # Apply automatic layout if requested
            if auto_layout:
                from labelbox.schema.workflow.workflow_utils import (
                    WorkflowLayoutManager,
                )

                WorkflowLayoutManager.reposition_nodes(workflow)
                # Get updated positions
                for i, node in enumerate(workflow.config.get("nodes", [])):
                    if i < len(work_config["nodes"]):
                        work_config["nodes"][i]["position"] = node.get(
                            "position", {"x": 0, "y": 0}
                        )

            # Save the clean API-compatible config to the server
            mutation = """
                mutation UpdateProjectWorkflowPyApi($input: UpdateProjectWorkflowInput!) {
                    updateProjectWorkflow(input: $input) {
                        projectId
                        config
                        createdAt
                        updatedAt
                    }
                }
            """

            # Create a properly structured input object
            input_obj = {
                "projectId": workflow.project_id,
                "config": work_config,
                "routeDataRows": [],
            }

            response = workflow.client.execute(
                mutation,
                {"input": input_obj},
            )

            # Extract updated data
            data = response.get("updateProjectWorkflow") or response.get(
                "data", {}
            ).get("updateProjectWorkflow")

            # Update timestamps if available
            if data:
                if "createdAt" in data:
                    workflow.created_at = datetime.fromisoformat(
                        data["createdAt"].replace("Z", "+00:00")
                    )
                if "updatedAt" in data:
                    workflow.updated_at = datetime.fromisoformat(
                        data["updatedAt"].replace("Z", "+00:00")
                    )
                if "config" in data:
                    workflow.config = data["config"]
                    # Reset caches
                    workflow._nodes_cache = None
                    workflow._edges_cache = None

            return workflow

        except Exception as e:
            # Reset caches in case of failure
            workflow._nodes_cache = None
            workflow._edges_cache = None
            logger.error(f"Error copying workflow: {e}")
            raise ValueError(f"Failed to copy workflow: {e}")

    @staticmethod
    def delete_nodes(
        workflow: "ProjectWorkflow", nodes: List[BaseWorkflowNode]
    ) -> "ProjectWorkflow":
        """Delete specified nodes from the workflow."""
        # Prevent deletion of initial nodes
        initial_node_types = [
            WorkflowDefinitionId.InitialLabelingTask,
            WorkflowDefinitionId.InitialReworkTask,
        ]

        for node in nodes:
            if node.definition_id in initial_node_types:
                node_type_name = (
                    "InitialLabeling"
                    if node.definition_id
                    == WorkflowDefinitionId.InitialLabelingTask
                    else "InitialRework"
                )
                raise ValueError(
                    f"Cannot delete {node_type_name} node (ID: {node.id}). "
                    f"Initial nodes are required for workflow validity. "
                    f"Use workflow.reset_to_initial_nodes() to create a new workflow instead."
                )

        # Get node IDs to remove
        node_ids = [node.id for node in nodes]

        # Remove nodes from config
        workflow.config["nodes"] = [
            n for n in workflow.config["nodes"] if n["id"] not in node_ids
        ]

        # Remove any edges connected to these nodes
        workflow.config["edges"] = [
            e
            for e in workflow.config["edges"]
            if e["source"] not in node_ids and e["target"] not in node_ids
        ]

        # Reset caches to ensure changes take effect
        workflow._nodes_cache = None
        workflow._edges_cache = None

        return workflow
