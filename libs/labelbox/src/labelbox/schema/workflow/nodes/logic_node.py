"""Logic node for conditional workflow routing based on configurable filters.

This module contains the LogicNode class which enables conditional branching
in workflows by applying filter logic to determine routing paths.
"""

import logging
from typing import Dict, List, Any, Optional, Literal
from pydantic import Field, model_validator, field_validator

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
    FilterField,
    FilterOperator,
)
from labelbox.schema.workflow.project_filter import (
    ProjectWorkflowFilter,
)

logger = logging.getLogger(__name__)

# Constants for this module
DEFAULT_FILTER_LOGIC_AND = "and"
DEFAULT_EMBEDDING_TYPE = "CLIPV2"


class LogicNode(BaseWorkflowNode):
    """Logic node. One or more instances possible. One input, two outputs (if/else)."""

    label: str = Field(
        default="Logic",
        description="Display name for the logic node",
        max_length=50,
    )
    filters: List[Dict[str, Any]] = Field(
        default_factory=lambda: [],
        description="Contains the logic conditions in user-friendly format",
    )
    filter_logic: Literal["and", "or"] = Field(
        default="and", alias="filterLogic"
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.Logic,
        frozen=True,
        alias="definitionId",
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Node instructions (stored as customFields.description in JSON)",
        frozen=True,  # Make instructions read-only
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )

    @model_validator(mode="after")
    def sync_filters_from_raw_data(self) -> "LogicNode":
        """Sync filters from raw_data if they exist there."""
        if not self.filters and "filters" in self.raw_data:
            # Load filters from raw_data if not already set
            raw_filters = self.raw_data["filters"]
            if isinstance(raw_filters, list):
                self.filters = raw_filters
        return self

    @property
    def config(self) -> Dict[str, Any]:
        """Returns the node's configuration including filters."""
        base_config = self.raw_data.copy()
        base_config["filters"] = self.filters
        return base_config

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v):
        """Validate that logic node has exactly one input."""
        if len(v) != 1:
            raise ValueError("Logic node must have exactly one input")
        return v

    def set_filters(self, filters: List[Dict[str, Any]]) -> "LogicNode":
        """Set the node's filters.

        Args:
            filters: List of filter dictionaries or user-friendly filter structures

        Returns:
            self for method chaining
        """
        # Process filters to convert from user-friendly formats to API format
        processed_filters = []

        # Handle ProjectWorkflowFilter object
        if hasattr(filters, "to_dict") and callable(filters.to_dict):
            # Extract the processed filters directly
            try:
                api_filters = filters.to_dict()
                if isinstance(api_filters, list):
                    processed_filters.extend(api_filters)
                    # Set filters and return without further processing
                    self.filters = processed_filters
                    self._sync_filters_to_workflow()
                    return self
            except Exception as e:
                logger.warning(
                    f"Error processing ProjectWorkflowFilter.to_dict(): {e}"
                )
        elif hasattr(filters, "filters") and isinstance(filters.filters, list):
            # Directly access 'filters' attribute if to_dict() failed or not available
            processed_filters.extend(filters.filters)
            self.filters = processed_filters
            self._sync_filters_to_workflow()
            return self

        # If not a ProjectWorkflowFilter or direct access failed, process each filter
        for filter_item in filters:
            # Handle special nl_search format
            if "nl_search" in filter_item and isinstance(
                filter_item["nl_search"], dict
            ):
                nl_data = filter_item["nl_search"]
                query = nl_data.get("query", "")
                # Initialize with defaults - never use None
                min_score = 0.0  # Default value
                max_score = 1.0  # Default value

                # Override with provided values if they exist
                if "min_score" in nl_data and nl_data["min_score"] is not None:
                    min_score = float(nl_data["min_score"])
                if "max_score" in nl_data and nl_data["max_score"] is not None:
                    max_score = float(nl_data["max_score"])

                embedding = nl_data.get("embedding", "CLIPV2")

                # Don't attempt to parse the query for a score value
                # Just use the original query string and the explicit min/max scores

                # Create the score object with guaranteed non-null values
                score_obj = {"min": min_score, "max": max_score}

                # Format the display value to include the score range
                display_value = f"{query} [{min_score} - {max_score}]"

                # Create NL search filter as a simple dict
                nl_filter = {
                    "field": FilterField.NlSearch,
                    "operator": FilterOperator.Is,
                    "value": display_value,
                    "metadata": {
                        "filter": {
                            "type": "nl_search",
                            "score": score_obj,
                            "content": query,
                            "embedding": embedding,
                        }
                    },
                }

                # Add the constructed filter to the list
                processed_filters.append(nl_filter)
            else:
                # Keep other filters as is
                processed_filters.append(filter_item)

        self.filters = processed_filters
        self._sync_filters_to_workflow()
        return self

    def clear_filters(self) -> "LogicNode":
        """Clear all filters."""
        self.filters = []
        self._sync_filters_to_workflow()
        return self

    def remove_filter_by_field(self, field_name: str) -> "LogicNode":
        """Remove filters by field name (backend field name like 'CreatedBy', 'Metadata', etc.).

        Args:
            field_name: The backend field name to remove (e.g., 'CreatedBy', 'Metadata', 'Sample')

        Returns:
            LogicNode: Self for method chaining

        Example:
            >>> logic.remove_filter_by_field('Sample')  # Remove sample probability filter
            >>> logic.remove_filter_by_field('Metadata')  # Remove metadata filters
        """
        if self.filters:
            # Filter out any filters with the specified field
            self.filters = [
                f for f in self.filters if f.get("field") != field_name
            ]
            self._sync_filters_to_workflow()
        return self

    def remove_filter(self, filter_field: FilterField) -> "LogicNode":
        """Remove filters by FilterField enum value.

        Args:
            filter_field: FilterField enum value specifying which filter type to remove
                         (e.g., FilterField.LabeledBy, FilterField.Sample, FilterField.LabelingTime)

        Returns:
            LogicNode: Self for method chaining

        Example:
            >>> from labelbox.schema.workflow import FilterField
            >>>
            >>> # Type-safe enum approach (required)
            >>> logic.remove_filter(FilterField.Sample)
            >>> logic.remove_filter(FilterField.LabeledBy)  # Consistent with labeled_by() function
            >>> logic.remove_filter(FilterField.LabelingTime)
            >>> logic.remove_filter(FilterField.Metadata)
        """
        # Use the FilterField enum value directly
        backend_field = filter_field.value

        if self.filters:
            # Filter out any filters with the specified field
            self.filters = [
                f for f in self.filters if f.get("field") != backend_field
            ]
            self._sync_filters_to_workflow()
        return self

    def _sync_filters_to_workflow(self) -> None:
        """Sync the current filters and filter_logic to the workflow config."""
        workflow = self.raw_data.get("_workflow")
        if workflow and hasattr(workflow, "config"):
            for node_data in workflow.config.get("nodes", []):
                if node_data.get("id") == self.id:
                    # Sync filters
                    if self.filters:
                        node_data["filters"] = self.filters
                    elif "filters" in node_data:
                        # Remove filters key if no filters
                        del node_data["filters"]

                    # Sync filter_logic
                    node_data["filterLogic"] = self.filter_logic
                    break

    def _sync_to_workflow(self) -> None:
        """Sync node properties to the workflow config."""
        workflow = self.raw_data.get("_workflow")
        if workflow and hasattr(workflow, "config"):
            for node_data in workflow.config.get("nodes", []):
                if node_data.get("id") == self.id:
                    # Update label
                    if hasattr(self, "label"):
                        node_data["label"] = self.label
                    # Update instructions via customFields
                    if (
                        hasattr(self, "instructions")
                        and self.instructions is not None
                    ):
                        if "customFields" not in node_data:
                            node_data["customFields"] = {}
                        node_data["customFields"]["description"] = (
                            self.instructions
                        )
                    # Update customFields
                    if hasattr(self, "custom_fields") and self.custom_fields:
                        node_data["customFields"] = self.custom_fields
                    break

    def get_parsed_filters(self) -> List[Dict[str, Any]]:
        """Get the parsed filters."""
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
                    # Ensure score is never null in filter section
                    if "filter" in metadata and metadata["filter"] is not None:
                        if metadata["filter"].get("score") is None:
                            # Create default score object
                            metadata["filter"]["score"] = {
                                "min": 0.0,
                                "max": 1.0,
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
                                    # Create default score object
                                    query_item["score"] = {
                                        "min": 0.0,
                                        "max": 1.0,
                                    }

        # Now parse the filters
        parsed_filters: List[Dict[str, Any]] = []
        for f in self.filters:
            if isinstance(f, dict) and f.get("field") == "NlSearch":
                # For NLSearch, create filter directly to avoid inheritance issues
                # Extract query from content or value
                query = ""
                min_score = 0.0
                max_score = 1.0

                if "metadata" in f and isinstance(f["metadata"], dict):
                    filter_section = f["metadata"].get("filter", {})
                    if isinstance(filter_section, dict):
                        if "content" in filter_section:
                            query = filter_section["content"]

                        # Extract score if available
                        score = filter_section.get("score")
                        if isinstance(score, dict):
                            min_score = score.get("min", 0.0)
                            max_score = score.get("max", 1.0)

                # If no query from metadata, try to get from value
                if not query and "value" in f:
                    value = f["value"]
                    if isinstance(value, str):
                        # Check if value has score range embedded
                        if "[" in value and "]" in value:
                            parts = value.split("[")
                            if len(parts) >= 2:
                                query = parts[0].strip()

                # Create NL search filter as a simple dict
                nl_filter = {
                    "field": FilterField.NlSearch,
                    "operator": f.get("operator", FilterOperator.Is),
                    "value": f"{query} [{min_score} - {max_score}]",
                    "metadata": {
                        "filter": {
                            "type": "nl_search",
                            "score": {"min": min_score, "max": max_score},
                            "content": query,
                            "embedding": "CLIPV2",
                        }
                    },
                }

                parsed_filters.append(nl_filter)
            else:
                # For other filters, use standard parsing
                parsed_filters.append(f)  # Just use the filter dict directly

        return parsed_filters

    def get_filters(self) -> "ProjectWorkflowFilter":
        """Get filters in user-friendly ProjectWorkflowFilter format.

        This method returns the filters in the original format.

        Returns:
            ProjectWorkflowFilter: Filters in user-friendly format

        Example:
            >>> logic = workflow.get_node_by_id("some-logic-node-id")
            >>> user_filters = logic.get_filters()
            >>> # Add a new filter
            >>> user_filters.append(labeled_by(["new-user-id"]))
            >>> # Apply the updated filters back to the node
            >>> logic.set_filters(user_filters)
        """
        from labelbox.schema.workflow.project_filter import (
            ProjectWorkflowFilter,
        )

        # For now, return empty ProjectWorkflowFilter since we simplified the system
        # TODO: Store original filter function rules to enable round-trip conversion
        return ProjectWorkflowFilter([])

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return [NodeOutput.If, NodeOutput.Else]

    def add_filter(self, filter_rule: Dict[str, Any]) -> "LogicNode":
        """Add a single filter using filter functions, replacing any existing filter of the same type.

        Args:
            filter_rule: Filter rule from filter functions
                        (e.g., labeled_by(["user_id"]), labeling_time.greater_than(300))

        Returns:
            LogicNode: Self for method chaining

        Example:
            >>> from labelbox.schema.workflow.project_filter import labeled_by, labeling_time, metadata, condition
            >>>
            >>> logic.add_filter(labeled_by(["user-123"]))
            >>> logic.add_filter(labeling_time.greater_than(300))
            >>> logic.add_filter(metadata([condition.contains("tag", "test")]))
            >>> # Adding another labeled_by filter will replace the previous one
            >>> logic.add_filter(labeled_by(["user-456"]))  # Replaces previous labeled_by filter
        """
        # Validate that this looks like filter function output
        if not self._is_filter_function_output(filter_rule):
            raise ValueError(
                "add_filter() only accepts output from filter functions. "
                "Use functions like labeled_by(), labeling_time.greater_than(), etc."
            )

        # Get the field name from the filter rule to check for existing filters
        field_name = list(filter_rule.keys())[0]

        # Convert filter function output to API format
        from labelbox.schema.workflow.filter_converters import (
            FilterAPIConverter,
        )

        converter = FilterAPIConverter()
        filter_result = converter.convert_to_api_format(filter_rule)

        # Convert FilterResult to dictionary for internal storage
        api_filter = {
            "field": filter_result.field,
            "value": filter_result.value,
            "operator": filter_result.operator,
        }

        if filter_result.metadata is not None:
            api_filter["metadata"] = filter_result.metadata

        if self.filters is None:
            self.filters = []

        # Remove any existing filter with the same field name
        self.filters = [f for f in self.filters if f.get("field") != field_name]

        # Add the new filter
        self.filters.append(api_filter)
        self._sync_filters_to_workflow()
        return self

    def _is_filter_function_output(self, filter_rule: Dict[str, Any]) -> bool:
        """Check if filter_rule is output from filter functions."""
        # Filter functions now return backend field names directly
        # Check if it has exactly one key that matches a known backend field
        if len(filter_rule) != 1:
            return False

        # Map backend field names to FilterField enum values
        backend_to_field = {
            "CreatedBy": FilterField.LabeledBy,  # Backend CreatedBy maps to user-facing LabeledBy
            "Annotation": FilterField.Annotation,
            "LabeledAt": FilterField.LabeledAt,
            "Sample": FilterField.Sample,
            "ConsensusAverage": FilterField.ConsensusAverage,
            "FeatureConsensusAverage": FilterField.FeatureConsensusAverage,
            "Dataset": FilterField.Dataset,
            "IssueCategory": FilterField.IssueCategory,
            "Batch": FilterField.Batch,
            "Metadata": FilterField.Metadata,
            "ModelPrediction": FilterField.ModelPrediction,
            "LabelingTime": FilterField.LabelingTime,
            "ReviewTime": FilterField.ReviewTime,
            "NlSearch": FilterField.NlSearch,
        }

        return list(filter_rule.keys())[0] in backend_to_field
