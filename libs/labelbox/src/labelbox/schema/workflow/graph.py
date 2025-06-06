"""Graph data structures and algorithms for Project Workflows in Labelbox.

This module provides graph-based operations for workflow validation, analysis,
and layout algorithms. It includes directed graph functionality and hierarchical
layout algorithms for workflow visualization.
"""

import logging
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class ProjectWorkflowGraph:
    """A directed graph implementation for workflow operations.

    This class provides the basic graph operations needed for workflow validation,
    path finding, and layout algorithms. It maintains both forward and backward
    adjacency lists for efficient traversal in both directions.

    Attributes:
        adjacency_list: Forward adjacency list (node -> list of successors)
        predecessors_map: Backward adjacency list (node -> list of predecessors)
        node_attrs: Dictionary storing node attributes (keys are the node IDs)
        edge_data: Dictionary storing edge metadata
    """

    def __init__(self) -> None:
        """Initialize an empty directed graph."""
        # Forward and reverse adjacency lists for efficient traversal
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)
        self.predecessors_map: Dict[str, List[str]] = defaultdict(list)

        # Node and edge storage
        self.node_attrs: Dict[str, Dict[str, Any]] = {}  # Store node attributes
        self.edge_data: Dict[
            Tuple[str, str], Dict[str, Any]
        ] = {}  # Track edge metadata

    def add_node(self, node_id: str, **attrs) -> None:
        """Add a node to the graph with optional attributes.

        Args:
            node_id: The node identifier
            **attrs: Optional attributes to associate with the node
        """
        if node_id not in self.node_attrs:
            self.node_attrs[node_id] = {}
        self.node_attrs[node_id].update(attrs)

    def add_edge(self, source: str, target: str, **attrs) -> bool:
        """Add a directed edge from source to target with optional attributes.

        Args:
            source: The source node identifier
            target: The target node identifier
            **attrs: Optional attributes to associate with the edge

        Returns:
            True if the edge was added, False if it already existed
        """
        # Check if edge already exists
        if target in self.adjacency_list[source]:
            logger.warning(
                f"Edge from {source} to {target} already exists. Ignoring duplicate."
            )
            return False

        # Add edge to both adjacency lists
        self.adjacency_list[source].append(target)
        self.predecessors_map[target].append(source)

        # Ensure both nodes are in the node_attrs
        if source not in self.node_attrs:
            self.node_attrs[source] = {}
        if target not in self.node_attrs:
            self.node_attrs[target] = {}

        # Store edge metadata if provided
        if attrs:
            self.edge_data[(source, target)] = attrs

        return True

    def predecessors(self, node_id: str) -> List[str]:
        """Return a list of predecessor nodes to the given node.

        Args:
            node_id: The node identifier

        Returns:
            List of nodes that have edges pointing to the given node
        """
        return list(self.predecessors_map.get(node_id, []))

    def successors(self, node_id: str) -> List[str]:
        """Return a list of successor nodes from the given node.

        Args:
            node_id: The node identifier

        Returns:
            List of nodes that the given node has edges pointing to
        """
        return list(self.adjacency_list.get(node_id, []))

    def in_degree(self, node_id: str) -> int:
        """Return the number of incoming edges to the given node.

        Args:
            node_id: The node identifier

        Returns:
            The number of incoming edges
        """
        return len(self.predecessors_map.get(node_id, []))


def hierarchical_layout(
    adjacency: Dict[str, List[str]],
    roots: List[str],
    x_spacing: int = 300,
    y_spacing: int = 150,
    top_margin: int = 50,
    left_margin: int = 50,
) -> Dict[str, Tuple[float, float]]:
    """Generate a hierarchical layout for a directed acyclic graph (DAG).

    This is a self-contained, O(n+e) layout algorithm that positions nodes
    in layers based on their depth from root nodes, with proper spacing
    to avoid overlaps.

    Args:
        adjacency: Dictionary mapping each node to its list of child nodes
        roots: List of entry nodes (nodes with no incoming edges)
        x_spacing: Horizontal distance between layers
        y_spacing: Vertical spacing unit for leaf nodes
        top_margin: Top margin offset for the overall graph
        left_margin: Left margin offset for the overall graph

    Returns:
        Dictionary mapping node IDs to (x, y) coordinate tuples
    """
    if not roots:
        return {}

    # Step 1: BFS to find the layer (depth) of each node
    depth: Dict[str, int] = {}
    node_queue: deque[str] = deque()

    # Initialize root nodes at depth 0
    for root in roots:
        depth[root] = 0
        node_queue.append(root)

    # Process nodes level by level
    while node_queue:
        current_node = node_queue.popleft()
        current_depth = depth[current_node]

        # Process all children
        for child in adjacency.get(current_node, []):
            new_depth = current_depth + 1
            # Only update if we haven't seen this node or found a shorter path
            if child not in depth or depth[child] > new_depth:
                depth[child] = new_depth
                node_queue.append(child)

    # Step 2: Compute subtree sizes (number of leaves under each node)
    size: Dict[str, int] = {}

    def calculate_subtree_size(node_id: str) -> int:
        """Calculate the size of the subtree rooted at node_id.

        Size is defined as the number of leaf nodes under this node.
        For leaf nodes, size is 1. For internal nodes, size is the
        sum of their children's sizes.

        Args:
            node_id: The identifier of the node

        Returns:
            The size of the subtree
        """
        if node_id in size:
            return size[node_id]

        children = adjacency.get(node_id, [])
        if not children:
            # Leaf node
            size[node_id] = 1
        else:
            # Internal node - sum of children's sizes
            size[node_id] = sum(
                calculate_subtree_size(child) for child in children
            )
        return size[node_id]

    # Calculate sizes for all nodes reachable from roots
    for root in roots:
        calculate_subtree_size(root)

    # Step 3: Recursively assign positions with parents centered over children
    positions: Dict[str, Tuple[float, float]] = {}

    def place(node_id: str, layer: int, start_y: float) -> None:
        """Place a node and its children in the layout.

        Places the node at the appropriate coordinates and recursively places
        all its children beneath it. Each parent is centered over its subtree.

        Args:
            node_id: The identifier of the node to place
            layer: The horizontal layer (depth) of the node
            start_y: The starting y-coordinate for this subtree
        """
        subtree_width = size[node_id] * y_spacing

        # Position this node at the center of its subtree
        center_y = start_y + subtree_width / 2
        center_x = left_margin + layer * x_spacing
        positions[node_id] = (center_x, top_margin + center_y)

        # Recursively place children, dividing the subtree space
        current_y = start_y
        for child in adjacency.get(node_id, []):
            place(child, layer + 1, current_y)
            current_y += size[child] * y_spacing

    # Step 4: Layout each root and its subtree
    y_cursor = 0
    for root in roots:
        place(root, 0, y_cursor)
        y_cursor += size[root] * y_spacing

    return positions
