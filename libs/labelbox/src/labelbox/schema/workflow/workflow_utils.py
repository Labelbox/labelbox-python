"""
Workflow utility functions for validation, layout, and serialization.

This module contains utility classes that support ProjectWorkflow operations
without directly manipulating the workflow structure.
"""

import json
import logging
from typing import Dict, List, Any, Optional, cast, TYPE_CHECKING
from collections import deque, defaultdict

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import WorkflowDefinitionId
from labelbox.schema.workflow.graph import ProjectWorkflowGraph
from labelbox.schema.workflow.nodes import LogicNode
from labelbox.schema.workflow.project_filter import convert_to_api_format

if TYPE_CHECKING:
    from labelbox.schema.workflow.workflow import ProjectWorkflow

logger = logging.getLogger(__name__)


class WorkflowValidator:
    """Validation utilities for workflow structure and nodes."""

    @staticmethod
    def validate_initial_nodes(
        nodes: List[BaseWorkflowNode],
    ) -> List[Dict[str, str]]:
        """Validate that workflow has exactly one InitialLabelingNode and one InitialReworkNode."""
        errors = []

        initial_labeling_nodes = [
            node
            for node in nodes
            if node.definition_id == WorkflowDefinitionId.InitialLabelingTask
        ]
        initial_rework_nodes = [
            node
            for node in nodes
            if node.definition_id == WorkflowDefinitionId.InitialReworkTask
        ]

        # Check InitialLabelingNode count
        if len(initial_labeling_nodes) == 0:
            errors.append(
                {
                    "node_type": "InitialLabelingNode",
                    "reason": "Workflow must have exactly one InitialLabelingNode, but found 0. Use workflow.reset_to_initial_nodes() to create required nodes.",
                    "node_id": "missing",
                }
            )
        elif len(initial_labeling_nodes) > 1:
            for node in initial_labeling_nodes:
                errors.append(
                    {
                        "node_type": "InitialLabelingNode",
                        "reason": f"Workflow must have exactly one InitialLabelingNode, but found {len(initial_labeling_nodes)}. Use workflow.reset_to_initial_nodes() to create a valid workflow.",
                        "node_id": node.id,
                    }
                )

        # Check InitialReworkNode count
        if len(initial_rework_nodes) == 0:
            errors.append(
                {
                    "node_type": "InitialReworkNode",
                    "reason": "Workflow must have exactly one InitialReworkNode, but found 0. Use workflow.reset_to_initial_nodes() to create required nodes.",
                    "node_id": "missing",
                }
            )
        elif len(initial_rework_nodes) > 1:
            for node in initial_rework_nodes:
                errors.append(
                    {
                        "node_type": "InitialReworkNode",
                        "reason": f"Workflow must have exactly one InitialReworkNode, but found {len(initial_rework_nodes)}. Use workflow.reset_to_initial_nodes() to create a valid workflow.",
                        "node_id": node.id,
                    }
                )

        return errors

    @staticmethod
    def validate_node_connections(
        nodes: List[BaseWorkflowNode], graph: Any
    ) -> List[Dict[str, str]]:
        """Validate node connections - incoming and outgoing."""
        errors = []

        initial_node_types = [
            WorkflowDefinitionId.InitialLabelingTask,
            WorkflowDefinitionId.InitialReworkTask,
        ]
        terminal_node_types = [
            WorkflowDefinitionId.Done,
            WorkflowDefinitionId.SendToRework,
            WorkflowDefinitionId.CustomReworkTask,
        ]

        # Check for unreachable nodes and incomplete paths
        for node in nodes:
            node_type = (
                node.definition_id.value if node.definition_id else "unknown"
            )

            # Check incoming connections (except initial nodes)
            if node.definition_id not in initial_node_types:
                predecessors = list(graph.predecessors(node.id))
                if not predecessors:
                    errors.append(
                        {
                            "reason": "has no incoming connections",
                            "node_id": node.id,
                            "node_type": node_type,
                        }
                    )
                elif len(predecessors) > 1:
                    # Check if all predecessors are initial nodes
                    node_map = {n.id: n for n in nodes}
                    predecessor_nodes = [
                        node_map.get(pred_id) for pred_id in predecessors
                    ]
                    all_initial = all(
                        pred_node
                        and pred_node.definition_id in initial_node_types
                        for pred_node in predecessor_nodes
                        if pred_node is not None
                    )

                    if not all_initial:
                        preds_info = ", ".join(
                            [p[:8] + "..." for p in predecessors]
                        )
                        errors.append(
                            {
                                "reason": f"has multiple incoming connections ({len(predecessors)}) but not all are from initial nodes",
                                "node_id": node.id,
                                "node_type": node_type,
                                "details": f"Connected from: {preds_info}",
                            }
                        )

            # Check outgoing connections (except terminal nodes)
            if node.definition_id not in terminal_node_types:
                successors = list(graph.successors(node.id))
                if not successors:
                    errors.append(
                        {
                            "reason": "has no outgoing connections",
                            "node_id": node.id,
                            "node_type": node_type,
                        }
                    )

        return errors

    @classmethod
    def validate(cls, workflow: "ProjectWorkflow") -> "ProjectWorkflow":
        """Validate the workflow graph structure to identify potential issues."""
        errors = []
        nodes = workflow.get_nodes()
        edges = workflow.get_edges()

        # Build graph for validation
        graph = ProjectWorkflowGraph()
        for edge in edges:
            graph.add_edge(edge.source, edge.target)

        # Check for validation errors
        initial_node_errors = cls.validate_initial_nodes(nodes)
        errors.extend(initial_node_errors)

        connection_errors = cls.validate_node_connections(nodes, graph)
        errors.extend(connection_errors)

        # Store validation results
        workflow._validation_errors = {"errors": errors}
        return workflow

    @staticmethod
    def check_validity(
        workflow: "ProjectWorkflow",
    ) -> Dict[str, List[Dict[str, str]]]:
        """Check the validity of the workflow configuration."""
        # Run validation
        WorkflowValidator.validate(workflow)
        # Return the validation errors
        return WorkflowValidator.get_validation_errors(workflow)

    @staticmethod
    def get_validation_errors(
        workflow: "ProjectWorkflow",
    ) -> Dict[str, List[Dict[str, str]]]:
        """Get validation errors from the most recent validation."""
        if "errors" not in workflow._validation_errors:
            # Run validation if not already done
            WorkflowValidator.validate(workflow)
        return workflow._validation_errors

    @staticmethod
    def format_validation_errors(
        validation_errors: Dict[str, List[Dict[str, str]]],
    ) -> str:
        """Format validation errors into a human-readable string."""
        errors = validation_errors.get("errors", [])
        if not errors:
            return ""

        error_details = []
        for error in errors:
            node_id = error.get("node_id", "unknown")
            node_type = error.get("node_type", "unknown")
            reason = error.get("reason", "unknown reason")

            # Extract additional details if available
            details = error.get("details", "")
            error_msg = f"Node {node_id[:8]}... ({node_type}) {reason}"
            if details:
                error_msg += f" - {details}"

            error_details.append(error_msg)

        return f"Workflow validation found the following issues: {'; '.join(error_details)}"


class WorkflowLayoutManager:
    """Layout management utilities for workflow visualization."""

    @staticmethod
    def reposition_nodes(
        workflow: "ProjectWorkflow",
        spacing_x: int = 400,
        spacing_y: int = 250,
        margin_x: int = 100,
        margin_y: int = 150,
    ) -> "ProjectWorkflow":
        """Reposition workflow nodes for better visual layout."""
        # Cache the list of node IDs
        nodes = [n["id"] for n in workflow.config.get("nodes", [])]

        if not nodes:
            return workflow

        # Build a graph of IDs → successors
        G = ProjectWorkflowGraph()
        for e in workflow.config.get("edges", []):
            G.add_edge(e["source"], e["target"])

        # 1) Find entry points (no incoming edges)
        entry = [nid for nid in nodes if G.in_degree(nid) == 0]
        if not entry:
            # if every node has a predecessor, just pick the minimal in-degree ones
            min_ind = min(G.in_degree(nid) for nid in nodes)
            entry = [nid for nid in nodes if G.in_degree(nid) == min_ind]

        # 2) BFS to assign each node a "layer" (depth)
        depth: Dict[str, Optional[int]] = {nid: None for nid in nodes}
        q: deque[str] = deque()
        for nid in entry:
            depth[nid] = 0
            q.append(nid)

        while q:
            u = q.popleft()
            # Get the depth of u, with a fallback to 0 if None (should not happen)
            u_depth: int = 0
            if depth[u] is not None:
                # Using cast to tell the type checker we're sure depth[u] is an int here
                u_depth = cast(int, depth[u])

            for v in G.successors(u):
                # first time we see it
                if depth[v] is None:
                    depth[v] = u_depth + 1
                    q.append(v)
                # we found a shorter path - ensure v_depth is not None before comparison
                elif depth[v] is not None:
                    # We know this is not None due to the check above
                    v_depth: int = cast(int, depth[v])
                    if v_depth > u_depth + 1:
                        depth[v] = u_depth + 1
                        q.append(v)

        # 3) Group nodes by layer
        layers: Dict[int, List[str]] = defaultdict(list)
        for nid, d in depth.items():
            # if still None (isolated), put them in layer 0
            layers[d or 0].append(nid)

        # 4) Compute (x,y) for each node
        pos: Dict[str, tuple] = {}
        for layer, ids in sorted(layers.items()):
            for idx, nid in enumerate(ids):
                x = margin_x + layer * spacing_x
                y = margin_y + idx * spacing_y
                pos[nid] = (x, y)

        # 5) Write back into workflow.config
        for node_data in workflow.config.get("nodes", []):
            nid = node_data.get("id")
            if nid in pos:
                x, y = pos[nid]
                node_data.setdefault("position", {})["x"] = x
                node_data.setdefault("position", {})["y"] = y

        # Invalidate any cache
        workflow._nodes_cache = None
        return workflow


class WorkflowSerializer:
    """Serialization utilities for workflow API communication."""

    @staticmethod
    def prepare_config_for_api(workflow: "ProjectWorkflow") -> Dict[str, Any]:
        """Prepare the workflow configuration for saving to the API."""
        # Make sure we include only fields that the API accepts
        clean_config = {
            "nodes": [
                {
                    key: value
                    for key, value in {
                        "id": node["id"],
                        "position": node["position"],
                        "definitionId": node["definitionId"],
                        "label": node.get("label"),
                        "filterLogic": node.get("filterLogic"),
                        "customFields": node.get("customFields"),
                        "config": node.get("config"),
                        "filters": WorkflowSerializer.serialize_filters(
                            node.get("filters")
                        ),
                    }.items()
                    if value is not None
                }
                for node in workflow.config.get("nodes", [])
            ],
            "edges": [
                {
                    "id": edge["id"],
                    "source": edge["source"],
                    "target": edge["target"],
                    "sourceHandle": edge["sourceHandle"],
                    "targetHandle": edge["targetHandle"],
                }
                for edge in workflow.config.get("edges", [])
            ],
        }
        return clean_config

    @staticmethod
    def serialize_filters(filters):
        """Serialize filters to ensure they are JSON-serializable."""
        if filters is None:
            return None

        # If it's a ProjectWorkflowFilter object, convert it to a list
        if hasattr(filters, "to_dict") and callable(filters.to_dict):
            try:
                return filters.to_dict()
            except Exception:
                # If to_dict() fails, try to access filters attribute directly
                if hasattr(filters, "filters") and isinstance(
                    filters.filters, list
                ):
                    return filters.filters

        # If it's already a list, we need to check if the filters are in API format
        if isinstance(filters, list):
            processed_filters = []
            for filter_item in filters:
                # Check if this filter is already in API format (has 'field', 'operator', 'value')
                if isinstance(filter_item, dict) and all(
                    key in filter_item for key in ["field", "operator", "value"]
                ):
                    # Already in API format, use as-is
                    processed_filters.append(filter_item)
                else:
                    # Not in API format, convert it
                    try:
                        filter_result = convert_to_api_format(filter_item)
                        # convert_to_api_format now returns a dict for backward compatibility
                        processed_filters.append(filter_result)
                    except Exception:
                        # If conversion fails, skip this filter
                        continue

            return processed_filters

        # For any other type, return None to avoid serialization errors
        return None

    @staticmethod
    def print_filters(workflow: "ProjectWorkflow") -> None:
        """Print the current filter configurations for all LogicNodes in the workflow."""
        logger.info("Current filter configurations in workflow nodes:")

        for node in workflow.get_nodes():
            if isinstance(node, LogicNode):
                logger.info(f"Filters for node {node.id} ({node.name}):")
                for i, f in enumerate(node.get_parsed_filters()):
                    logger.info(f"  Filter {i+1}:")
                    logger.info(f"  {json.dumps(f, indent=2)}")
