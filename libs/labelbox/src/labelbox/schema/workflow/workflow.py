"""
Project Workflow implementation for Labelbox.

This module contains the main ProjectWorkflow class that handles workflow configuration
for projects, providing access to strongly-typed nodes and edges.
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
    ForwardRef,
    Union,
    Literal,
    overload,
    NamedTuple,
)
from pydantic import BaseModel, ConfigDict, PrivateAttr

from labelbox.schema.workflow.base import BaseWorkflowNode, NodePosition
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeType,
    NodeOutput,
    NodeInput,
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
    UnknownWorkflowNode,
    LogicNode,
    AutoQANode,
)
from labelbox.schema.workflow.project_filter import ProjectWorkflowFilter
from labelbox.schema.workflow.config import LabelingConfig, ReworkConfig

# Import the utility classes
from labelbox.schema.workflow.workflow_utils import (
    WorkflowValidator,
    WorkflowLayoutManager,
    WorkflowSerializer,
)
from labelbox.schema.workflow.workflow_operations import (
    WorkflowOperations,
    NODE_TYPE_MAP,
)

logger = logging.getLogger(__name__)


class InitialNodes(NamedTuple):
    """Container for the two required initial workflow nodes.

    Attributes:
        labeling: InitialLabeling node for new data entering workflow
        rework: InitialRework node for rejected data needing corrections
    """

    labeling: InitialLabelingNode
    rework: InitialReworkNode


def _validate_definition_id(
    definition_id_str: str, node_id: str
) -> WorkflowDefinitionId:
    """Validate and normalize a workflow definition ID.

    Args:
        definition_id_str: The definition ID string to validate
        node_id: Node ID for error reporting

    Returns:
        WorkflowDefinitionId: Validated definition ID or fallback
    """
    try:
        return WorkflowDefinitionId(definition_id_str)
    except ValueError as e:
        logger.warning(
            f"Invalid WorkflowDefinitionId '{definition_id_str}' for node {node_id}: {e}. "
            f"Using InitialLabelingTask as fallback."
        )
        return WorkflowDefinitionId.InitialLabelingTask


def _get_definition_id_for_class(
    NodeClass: Type[BaseWorkflowNode],
) -> WorkflowDefinitionId:
    """Get the appropriate WorkflowDefinitionId for a given node class.

    Args:
        NodeClass: The node class to get definition ID for

    Returns:
        WorkflowDefinitionId: The corresponding definition ID
    """
    # Check NODE_TYPE_MAP for direct mapping
    for enum_val, mapped_class in NODE_TYPE_MAP.items():
        if mapped_class == NodeClass:
            return enum_val

    # Fallback mapping based on class inheritance
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

    logger.warning(
        f"Could not determine definitionId for {NodeClass.__name__}. "
        f"Using InitialLabelingTask as default."
    )
    return WorkflowDefinitionId.InitialLabelingTask


# Create a forward reference for WorkflowEdge to avoid circular imports
WorkflowEdge = ForwardRef("labelbox.schema.workflow.edges.WorkflowEdge")


class ProjectWorkflow(BaseModel):
    """A ProjectWorkflow represents the workflow configuration for a project,
    providing access to strongly-typed nodes and edges.
    """

    client: Any  # Using Any instead of "Client" to avoid type checking issues
    project_id: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Private attributes for caching
    _nodes_cache: Optional[List[BaseWorkflowNode]] = PrivateAttr(default=None)
    _edges_cache: Optional[List[Any]] = PrivateAttr(
        default=None
    )  # Use Any to avoid circular imports
    _edge_factory: Optional[Any] = PrivateAttr(default=None)
    _validation_errors: Dict[str, Any] = PrivateAttr(default={"errors": []})

    @classmethod
    def get_workflow(cls, client: Any, project_id: str) -> "ProjectWorkflow":
        """Get the workflow configuration for a project.

        Args:
            client: The Labelbox client
            project_id (str): The ID of the project

        Returns:
            ProjectWorkflow: The project workflow object with parsed nodes

        Raises:
            ValueError: If workflow not found for the project ID
        """
        query_str = """
        query GetProjectWorkflowPyApi($projectId: ID!) {
          projectWorkflow(projectId: $projectId) {
            projectId
            config
            createdAt
            updatedAt
          }
        }
        """

        response = client.execute(query_str, {"projectId": project_id})
        workflow_data = response["projectWorkflow"]
        if workflow_data is None:
            raise ValueError(f"Workflow not found for project ID: {project_id}")

        # Ensure timezone info for proper parsing
        created_at_str = workflow_data["createdAt"]
        if not created_at_str.endswith("Z"):
            created_at_str += "Z"
        updated_at_str = workflow_data["updatedAt"]
        if not updated_at_str.endswith("Z"):
            updated_at_str += "Z"

        return cls(
            client=client,
            project_id=workflow_data["projectId"],
            config=workflow_data["config"],
            created_at=datetime.fromisoformat(
                created_at_str.replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                updated_at_str.replace("Z", "+00:00")
            ),
        )

    def __init__(self, **data):
        super().__init__(**data)

        # Ensure config has required properties
        if "config" not in data or data["config"] is None:
            self.config = {"nodes": [], "edges": []}
        elif not isinstance(self.config, dict):
            self.config = {"nodes": [], "edges": []}
        else:
            # Ensure config.nodes exists
            if "nodes" not in self.config:
                self.config["nodes"] = []
            # Ensure config.edges exists
            if "edges" not in self.config:
                logger.info("Initializing empty edges array in config")
                self.config["edges"] = []

        # Initialize edge factory
        from labelbox.schema.workflow.edges import WorkflowEdgeFactory

        self._edge_factory = WorkflowEdgeFactory(self)

    def __repr__(self) -> str:
        """Return a concise string representation of the workflow."""
        node_count = len(self.config.get("nodes", []))
        edge_count = len(self.config.get("edges", []))
        return f"ProjectWorkflow(project_id='{self.project_id}', nodes={node_count}, edges={edge_count})"

    def __str__(self) -> str:
        """Return a detailed string representation of the workflow."""
        return self.__repr__()

    def get_node_by_id(self, node_id: str) -> Optional[BaseWorkflowNode]:
        """Get a node by its ID."""
        return next(
            (node for node in self.get_nodes() if node.id == node_id), None
        )

    def get_nodes(self) -> List[BaseWorkflowNode]:
        """Get all nodes in the workflow, parsed into their respective node classes."""
        if self._nodes_cache is not None:
            return self._nodes_cache

        nodes = []
        for node_data in self.config.get("nodes", []):
            node_id = node_data.get("id", "")
            definition_id_str = node_data.get("definitionId", "")

            definition_id = _validate_definition_id(definition_id_str, node_id)
            node_class = NODE_TYPE_MAP.get(definition_id, UnknownWorkflowNode)

            try:
                position = node_data.get("position", {"x": 0, "y": 0})

                # Build node constructor arguments from config data
                node_kwargs = {
                    "id": node_id,
                    "position": NodePosition(**position),
                    "definitionId": definition_id,
                    "raw_data": node_data,
                }

                # Extract optional properties if present
                if "label" in node_data:
                    node_kwargs["label"] = node_data["label"]

                if "filterLogic" in node_data:
                    node_kwargs["filterLogic"] = node_data["filterLogic"]

                if "filters" in node_data:
                    node_kwargs["filters"] = node_data["filters"]

                if "config" in node_data:
                    node_kwargs["config"] = node_data["config"]

                if "customFields" in node_data:
                    node_kwargs["customFields"] = node_data["customFields"]

                    # Extract instructions from customFields if available
                    custom_fields = node_data["customFields"]
                    if (
                        isinstance(custom_fields, dict)
                        and "description" in custom_fields
                    ):
                        node_kwargs["instructions"] = custom_fields[
                            "description"
                        ]

                # Extract assignment fields
                if "groupAssignment" in node_data:
                    node_kwargs["groupAssignment"] = node_data[
                        "groupAssignment"
                    ]

                if "individualAssignment" in node_data:
                    node_kwargs["individualAssignment"] = node_data[
                        "individualAssignment"
                    ]

                # Extract input/output fields
                if "inputs" in node_data:
                    node_kwargs["inputs"] = node_data["inputs"]

                if "output_if" in node_data:
                    node_kwargs["output_if"] = node_data["output_if"]

                if "output_else" in node_data:
                    node_kwargs["output_else"] = node_data["output_else"]

                # Store workflow reference for synchronization
                node_kwargs["raw_data"]["_workflow"] = self

                node = node_class(**node_kwargs)
                nodes.append(node)
            except Exception as e:
                logger.warning(
                    f"Failed to create node {node_id} of type {definition_id}: {e}. "
                    f"Creating UnknownWorkflowNode instead."
                )
                try:
                    node = UnknownWorkflowNode(
                        id=node_id,
                        position=NodePosition(**position),
                        definitionId=WorkflowDefinitionId.Unknown,
                        raw_data=node_data,
                    )
                    nodes.append(node)
                except Exception as e2:
                    logger.error(
                        f"Failed to create fallback UnknownWorkflowNode for {node_id}: {e2}"
                    )

        self._nodes_cache = nodes
        return nodes

    def get_edges(self) -> List[Any]:  # Any to avoid circular import issues
        """Get all edges in the workflow."""
        if self._edges_cache is not None:
            return self._edges_cache

        edges = []
        if self._edge_factory:
            for edge_data in self.config.get("edges", []):
                try:
                    edge = self._edge_factory.create_edge(edge_data)
                    edges.append(edge)
                except Exception as e:
                    logger.warning(
                        f"Failed to create edge {edge_data.get('id', 'unknown')}: {e}"
                    )

        self._edges_cache = edges
        return edges

    def add_edge(
        self,
        source_node: BaseWorkflowNode,
        target_node: BaseWorkflowNode,
        source_handle: NodeOutput = NodeOutput.If,
        target_handle: NodeInput = NodeInput.Default,
    ) -> Any:  # Any to avoid circular import issues
        """Add an edge connecting two nodes in the workflow."""
        if not self._edge_factory:
            raise ValueError("Edge factory not initialized")

        edge = self._edge_factory(source_node, target_node, source_handle)

        # Clear caches to ensure consistency
        self._edges_cache = None
        self._nodes_cache = None

        return edge

    # Validation methods
    def check_validity(self) -> Dict[str, List[Dict[str, str]]]:
        """Check the validity of the workflow configuration."""
        return WorkflowValidator.check_validity(self)

    def get_validation_errors(self) -> Dict[str, List[Dict[str, str]]]:
        """Get validation errors for the workflow."""
        return WorkflowValidator.get_validation_errors(self)

    @staticmethod
    def format_validation_errors(
        validation_errors: Dict[str, List[Dict[str, str]]],
    ) -> str:
        """Format validation errors for display."""
        return WorkflowValidator.format_validation_errors(validation_errors)

    @classmethod
    def validate(cls, workflow: "ProjectWorkflow") -> "ProjectWorkflow":
        """Validate a workflow and store validation results."""
        return WorkflowValidator.validate(workflow)

    def update_config(self, reposition: bool = True) -> "ProjectWorkflow":
        """Update the workflow configuration on the server.

        This method automatically validates the workflow before updating to ensure
        data integrity and prevent invalid configurations from being saved.

        Args:
            reposition: Whether to automatically reposition nodes before update

        Returns:
            ProjectWorkflow: Updated workflow instance

        Raises:
            ValueError: If validation errors are found or the update operation fails
        """
        try:
            # Always validate workflow before updating (mandatory for data safety)
            validation_result = self.check_validity()
            validation_errors = validation_result.get("errors", [])

            if validation_errors:
                # Format validation errors for clear user feedback
                formatted_errors = self.format_validation_errors(
                    validation_result
                )
                logger.error(f"Workflow validation failed: {formatted_errors}")

                # Raise a clear ValueError with validation details
                raise ValueError(
                    f"Cannot update workflow configuration due to validation errors:\n{formatted_errors}\n\n"
                    f"Please fix these issues before updating."
                )

            if reposition:
                self.reposition_nodes()

            api_config = WorkflowSerializer.prepare_config_for_api(self)

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

            input_obj = {
                "projectId": self.project_id,
                "config": api_config,
                "routeDataRows": [],
            }

            response = self.client.execute(
                mutation,
                {"input": input_obj},
            )

            data = response.get("updateProjectWorkflow") or response.get(
                "data", {}
            ).get("updateProjectWorkflow")

            # Update instance with server response
            if data:
                if "createdAt" in data:
                    self.created_at = datetime.fromisoformat(
                        data["createdAt"].replace("Z", "+00:00")
                    )
                if "updatedAt" in data:
                    self.updated_at = datetime.fromisoformat(
                        data["updatedAt"].replace("Z", "+00:00")
                    )
                if "config" in data:
                    self.config = data["config"]
                    self._nodes_cache = None
                    self._edges_cache = None

            return self

        except Exception as e:
            self._nodes_cache = None
            self._edges_cache = None
            logger.error(f"Error updating workflow: {e}")
            raise ValueError(f"Failed to update workflow: {e}")

    # Workflow management operations
    def reset_to_initial_nodes(
        self,
        labeling_config: Optional[LabelingConfig] = None,
        rework_config: Optional[ReworkConfig] = None,
    ) -> InitialNodes:
        """Reset workflow and create the two required initial nodes.

        IMPORTANT: This method preserves existing initial node IDs to prevent workflow breakage.
        It only creates new IDs for truly new workflows (first-time setup).

        Clears all non-initial nodes and edges, then creates/updates:
        - InitialLabeling node: Entry point for new data requiring labeling
        - InitialRework node: Entry point for rejected data requiring corrections

        Args:
            labeling_config: Configuration for InitialLabeling node
            rework_config: Configuration for InitialRework node

        Returns:
            InitialNodes with labeling and rework nodes ready for workflow building

        Example:
            >>> initial_nodes = workflow.reset_to_initial_nodes(
            ...     labeling_config=LabelingConfig(instructions="Label all objects", max_contributions_per_user=10),
            ...     rework_config=ReworkConfig(individual_assignment=["user-id-123"])
            ... )
            >>> done = workflow.add_node(type=NodeType.Done)
            >>> workflow.add_edge(initial_nodes.labeling, done)
            >>> workflow.add_edge(initial_nodes.rework, done)
        """
        # Convert configs to dicts for node creation
        labeling_dict = (
            labeling_config.model_dump(exclude_none=True)
            if labeling_config
            else {}
        )
        rework_dict = (
            rework_config.model_dump(exclude_none=True) if rework_config else {}
        )

        # Find existing initial nodes to preserve their IDs
        existing_labeling_id = None
        existing_rework_id = None

        for node_data in self.config.get("nodes", []):
            definition_id = node_data.get("definitionId")
            if definition_id == WorkflowDefinitionId.InitialLabelingTask.value:
                existing_labeling_id = node_data.get("id")
            elif definition_id == WorkflowDefinitionId.InitialReworkTask.value:
                existing_rework_id = node_data.get("id")

        # Reset workflow configuration (clear all nodes and edges)
        self.config = {"nodes": [], "edges": []}
        self._nodes_cache = None
        self._edges_cache = None

        # Create/recreate initial nodes, preserving existing IDs if they exist
        if existing_labeling_id:
            labeling_dict["id"] = existing_labeling_id
        if existing_rework_id:
            rework_dict["id"] = existing_rework_id

        # Create required initial nodes using internal method
        initial_labeling = cast(
            InitialLabelingNode,
            self._create_node_internal(InitialLabelingNode, **labeling_dict),
        )
        initial_rework = cast(
            InitialReworkNode,
            self._create_node_internal(InitialReworkNode, **rework_dict),
        )

        return InitialNodes(labeling=initial_labeling, rework=initial_rework)

    def delete_nodes(self, nodes: List[BaseWorkflowNode]) -> "ProjectWorkflow":
        """Delete specified nodes from the workflow."""
        return WorkflowOperations.delete_nodes(self, nodes)

    @classmethod
    def copy_workflow_structure(
        cls,
        source_workflow: "ProjectWorkflow",
        target_client,
        target_project_id: str,
    ) -> "ProjectWorkflow":
        """Copy the workflow structure from a source workflow to a new project.

        IMPORTANT: This method preserves existing initial node IDs to prevent workflow breakage.
        Changing initial node IDs will completely break the workflow and require support intervention.
        """
        return WorkflowOperations.copy_workflow_structure(
            source_workflow, target_client, target_project_id
        )

    def copy_from(
        self, source_workflow: "ProjectWorkflow", auto_layout: bool = True
    ) -> "ProjectWorkflow":
        """Copy the nodes and edges from a source workflow to this workflow.

        IMPORTANT: This method preserves existing initial node IDs to prevent workflow breakage.
        Changing initial node IDs will completely break the workflow and require support intervention.
        """
        return WorkflowOperations.copy_from(self, source_workflow, auto_layout)

    # Layout and display methods
    def reposition_nodes(
        self,
        spacing_x: int = 400,
        spacing_y: int = 250,
        margin_x: int = 100,
        margin_y: int = 150,
    ) -> "ProjectWorkflow":
        """Reposition nodes in the workflow using automatic layout."""
        return WorkflowLayoutManager.reposition_nodes(
            self, spacing_x, spacing_y, margin_x, margin_y
        )

    def print_filters(self) -> "ProjectWorkflow":
        """Print filter information for Logic nodes in the workflow."""
        WorkflowSerializer.print_filters(self)
        return self

    def _get_node_position(
        self,
        after_node_id: Optional[str] = None,
        default_x: float = 0,
        default_y: float = 0,
    ) -> NodePosition:
        """Get the position for a new node.

        Args:
            after_node_id: Optional ID of a node to position this node after
            default_x: Default x-coordinate if not positioned after another node
            default_y: Default y-coordinate if not positioned after another node

        Returns:
            NodePosition: Position coordinates for the new node
        """
        if after_node_id:
            after_node = self.get_node_by_id(after_node_id)
            if after_node:
                return NodePosition(
                    x=after_node.position.x + 250,
                    y=after_node.position.y,
                )
        return NodePosition(x=default_x, y=default_y)

    def _create_node_internal(
        self,
        NodeClass: Type[BaseWorkflowNode],
        x: Optional[float] = None,
        y: Optional[float] = None,
        after_node_id: Optional[str] = None,
        **kwargs,
    ) -> BaseWorkflowNode:
        """Internal method to create a node with proper position and ID.

        Args:
            NodeClass: The class of node to create
            x: Optional x-coordinate for the node position
            y: Optional y-coordinate for the node position
            after_node_id: Optional ID of a node to position this node after
            **kwargs: Additional parameters to pass to the node constructor

        Returns:
            BaseWorkflowNode: The created workflow node
        """
        node_id = kwargs.pop("id", f"{uuid.uuid4()}")

        # Normalize parameter names for consistency
        if "name" in kwargs and "label" not in kwargs:
            kwargs["label"] = kwargs.pop("name")

        position = self._get_node_position(after_node_id, x or 0, y or 0)

        definition_id = kwargs.pop("definition_id", None)
        if definition_id is None:
            definition_id = _get_definition_id_for_class(NodeClass)

        # Prepare node constructor arguments
        raw_data = kwargs.copy()
        constructor_args = {
            "id": node_id,
            "position": position,
            "definitionId": definition_id,
            "raw_data": raw_data,
        }
        constructor_args.update(kwargs)

        node = NodeClass(**constructor_args)
        node.raw_data["_workflow"] = self

        # Handle unknown definition IDs
        if node.definition_id == WorkflowDefinitionId.Unknown:
            logger.warning(
                f"Node {node.id} has Unknown definition_id. "
                f"Setting to InitialLabelingTask to prevent API errors."
            )
            node.raw_data["definitionId"] = (
                WorkflowDefinitionId.InitialLabelingTask.value
            )

        # Build node data for config storage
        node_data = {
            "id": node.id,
            "position": node.position.model_dump(),
            "definitionId": (
                WorkflowDefinitionId.InitialLabelingTask.value
                if node.definition_id == WorkflowDefinitionId.Unknown
                else node.definition_id.value
            ),
        }

        # Add optional node properties to config
        if hasattr(node, "label") and node.label:
            node_data["label"] = node.label

        if hasattr(node, "filter_logic") and node.filter_logic:
            node_data["filterLogic"] = node.filter_logic

        if hasattr(node, "custom_fields") and node.custom_fields:
            node_data["customFields"] = node.custom_fields

        if hasattr(node, "node_config") and node.node_config:
            node_data["config"] = node.node_config

        if hasattr(node, "filters") and node.filters:
            node_data["filters"] = node.filters

        if hasattr(node, "inputs") and node.inputs:
            node_data["inputs"] = node.inputs

        self.config["nodes"].append(node_data)
        self._nodes_cache = None

        return node

    # Type overloads for add_node method with node-specific parameters

    @overload
    def add_node(
        self,
        *,
        type: Literal[NodeType.Review],
        name: str = "Review task",
        instructions: Optional[str] = None,
        group_assignment: Optional[Union[str, List[str], Any]] = None,
        max_contributions_per_user: Optional[int] = None,
        **kwargs,
    ) -> ReviewNode: ...

    @overload
    def add_node(
        self, *, type: Literal[NodeType.Rework], name: str = "Rework", **kwargs
    ) -> ReworkNode: ...

    @overload
    def add_node(
        self,
        *,
        type: Literal[NodeType.Logic],
        name: str = "Logic",
        filters: Optional[
            Union[List[Dict[str, Any]], ProjectWorkflowFilter]
        ] = None,
        match_filters: MatchFilters = MatchFilters.All,
        **kwargs,
    ) -> LogicNode: ...

    @overload
    def add_node(
        self, *, type: Literal[NodeType.Done], name: str = "Done", **kwargs
    ) -> DoneNode: ...

    @overload
    def add_node(
        self,
        *,
        type: Literal[NodeType.CustomRework],
        name: str = "",
        instructions: Optional[str] = None,
        group_assignment: Optional[Union[str, List[str], Any]] = None,
        individual_assignment: Optional[Union[str, List[str]]] = None,
        max_contributions_per_user: Optional[int] = None,
        **kwargs,
    ) -> CustomReworkNode: ...

    @overload
    def add_node(
        self,
        *,
        type: Literal[NodeType.AutoQA],
        name: str = "Label Score (AutoQA)",
        evaluator_id: str,
        scope: Scope = Scope.All,
        score_name: str,
        score_threshold: float,
        **kwargs,
    ) -> AutoQANode: ...

    def add_node(self, *, type: NodeType, **kwargs) -> BaseWorkflowNode:
        """Add a node to the workflow with type-specific parameters."""
        # Block manual creation of initial nodes
        if type in [NodeType.InitialLabeling, NodeType.InitialRework]:
            raise ValueError(
                f"Cannot create {type.value} nodes via add_node(). "
                f"Use workflow.reset_to_initial_nodes() instead."
            )

        workflow_def_id = WorkflowDefinitionId(type.value)
        node_class = NODE_TYPE_MAP[workflow_def_id]

        processed_kwargs = kwargs.copy()

        # Normalize parameter names
        if "name" in processed_kwargs:
            processed_kwargs["label"] = processed_kwargs.pop("name")

        # Handle LogicNode-specific parameter transformations
        if type == NodeType.Logic and "match_filters" in processed_kwargs:
            match_filters_value = processed_kwargs.pop("match_filters")
            if match_filters_value == MatchFilters.Any:
                processed_kwargs["filter_logic"] = "or"
            else:  # MatchFilters.All
                processed_kwargs["filter_logic"] = "and"

        if type == NodeType.Logic and "filters" in processed_kwargs:
            filters_value = processed_kwargs["filters"]
            if hasattr(filters_value, "to_dict") and callable(
                filters_value.to_dict
            ):
                try:
                    processed_kwargs["filters"] = filters_value.to_dict()
                except Exception:
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
            # Handled by the node's model validator
            pass

        # Remove internal fields that should not be set directly by users
        processed_kwargs.pop("custom_fields", None)
        if type != NodeType.Logic:  # LogicNode filter_logic is handled above
            processed_kwargs.pop("filter_logic", None)

        return self._create_node_internal(
            cast(Type[BaseWorkflowNode], node_class), **processed_kwargs
        )
