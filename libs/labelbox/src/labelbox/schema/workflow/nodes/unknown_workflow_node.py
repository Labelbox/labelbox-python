"""Fallback node for unrecognized or unsupported node types."""

import logging
from typing import Dict, List, Any, Optional, Literal
from pydantic import Field

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
    FilterField,
    FilterOperator,
)

logger = logging.getLogger(__name__)

# Module-level constants
DEFAULT_EMBEDDING_TYPE = "CLIPV2"
DEFAULT_MIN_SCORE = 0.0
DEFAULT_MAX_SCORE = 1.0


class UnknownWorkflowNode(BaseWorkflowNode):
    """
    Fallback node for unrecognized or unsupported node types.

    This node serves as a safety fallback when encountering workflow configurations
    with node types that are not recognized by the current system. It preserves
    the original node data while providing a stable interface for workflow operations.

    Attributes:
        label (str): Display name for the node (default: "")
        node_config (Optional[List[Dict[str, Any]]]): Original node configuration
        filters (Optional[List[Dict[str, Any]]]): Original filter configuration
        filter_logic (Optional[str]): Logic for combining filters ("and" or "or")
        custom_fields (Dict[str, Any]): Additional custom configuration
        definition_id (WorkflowDefinitionId): Node type identifier (read-only, Unknown)

    Inputs:
        Variable: Preserves original input configuration

    Outputs:
        None: Unknown nodes have no defined outputs for safety

    Behavior:
        - Preserves all original node data without modification
        - Provides stable interface for workflow operations
        - Prevents workflow corruption when encountering unknown node types
        - Enables forward compatibility with newer node types

    Use Cases:
        - Loading workflows created with newer system versions
        - Handling experimental or custom node types
        - Maintaining workflow integrity during system upgrades
        - Debugging workflow configurations with unrecognized nodes

    Filter Support:
        UnknownWorkflowNode includes special filter handling to maintain
        compatibility with various filter formats, including NL Search.

    Example:
        >>> # Unknown nodes are created automatically during workflow loading
        >>> for node in workflow.nodes:
        ...     if isinstance(node, UnknownWorkflowNode):
        ...         print(f"Unknown node: {node.label} (ID: {node.id})")
        ...         print(f"Original config: {node.node_config}")

    Note:
        Unknown nodes should be reviewed and either converted to supported
        node types or handled appropriately in workflow logic. They serve
        as a safety mechanism to prevent data loss during parsing.
    """

    label: str = Field(default="", max_length=50)
    node_config: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="config"
    )
    filters: Optional[List[Dict[str, Any]]] = None
    filter_logic: Optional[Literal["and", "or"]] = Field(
        default=None, alias="filterLogic"
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.Unknown,
        frozen=True,
        alias="definitionId",
    )

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return []  # Unknown nodes have no defined outputs

    def get_parsed_filters(self) -> List[Dict[str, Any]]:
        """Get the parsed filters with special handling for NL search."""
        if not self.filters:
            return []

        # First ensure that NLSearch filters have a proper score
        for f in self.filters:
            if (
                isinstance(f, dict)
                and f.get("field") == "NlSearch"
                and "metadata" in f
            ):
                metadata = f.get("metadata", {})
                if isinstance(metadata, dict):
                    # Ensure score is never null in main filter section
                    if "filter" in metadata and metadata["filter"] is not None:
                        if metadata["filter"].get("score") is None:
                            # Create default score object to prevent null errors
                            metadata["filter"]["score"] = {
                                "min": DEFAULT_MIN_SCORE,
                                "max": DEFAULT_MAX_SCORE,
                            }

                    # Ensure score is never null in searchQuery section
                    if "searchQuery" in metadata and isinstance(
                        metadata["searchQuery"], dict
                    ):
                        query_list = metadata["searchQuery"].get("query", [])
                        if isinstance(query_list, list):
                            for query_item in query_list:
                                if (
                                    isinstance(query_item, dict)
                                    and query_item.get("score") is None
                                ):
                                    # Create default score object for query item
                                    query_item["score"] = {
                                        "min": DEFAULT_MIN_SCORE,
                                        "max": DEFAULT_MAX_SCORE,
                                    }

        # Main parsing: Process each filter for API compatibility
        parsed_filters: List[Dict[str, Any]] = []
        for f in self.filters:
            if isinstance(f, dict) and f.get("field") == "NlSearch":
                # Special handling for NLSearch filters
                # Extract query content and score information
                query = ""
                min_score = DEFAULT_MIN_SCORE
                max_score = DEFAULT_MAX_SCORE

                if "metadata" in f and isinstance(f["metadata"], dict):
                    filter_section = f["metadata"].get("filter", {})
                    if isinstance(filter_section, dict):
                        # Get query content from filter metadata
                        if "content" in filter_section:
                            query = filter_section["content"]

                        # Extract score range if available
                        score = filter_section.get("score")
                        if isinstance(score, dict):
                            min_score = score.get("min", DEFAULT_MIN_SCORE)
                            max_score = score.get("max", DEFAULT_MAX_SCORE)

                # Fallback: extract query from value field if not in metadata
                if not query and "value" in f:
                    value = f["value"]
                    if isinstance(value, str):
                        # Check if value has embedded score range format
                        if "[" in value and "]" in value:
                            parts = value.split("[")
                            if len(parts) >= 2:
                                query = parts[0].strip()

                # Construct standardized NL search filter
                nl_filter = {
                    "field": FilterField.NlSearch,
                    "operator": f.get("operator", FilterOperator.Is),
                    "value": f"{query} [{min_score} - {max_score}]",
                    "metadata": {
                        "filter": {
                            "type": "nl_search",
                            "score": {"min": min_score, "max": max_score},
                            "content": query,
                            "embedding": DEFAULT_EMBEDDING_TYPE,
                        }
                    },
                }

                parsed_filters.append(nl_filter)
            else:
                # For other filters, use standard parsing
                parsed_filters.append(f)  # Just use the filter dict directly

        return parsed_filters
