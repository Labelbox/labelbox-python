"""Refactored filter conversion logic with improved maintainability."""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .filter_utils import (
    format_time_duration,
    format_datetime_display,
    build_metadata_items,
    get_custom_label_or_count,
)
from .enums import FilterOperator
from labelbox.schema.workflow.base import (
    format_metadata_operator,
)


@dataclass
class FilterResult:
    """Strongly-typed result from filter conversion."""

    field: str
    value: str
    operator: FilterOperator
    metadata: Optional[Any] = None


class FilterConverter(ABC):
    """Abstract base class for filter converters."""

    @abstractmethod
    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        """Convert a filter to API format."""
        pass


class CreatedByFilterConverter(FilterConverter):
    """Handles CreatedBy filter conversion."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, list):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        user_ids = value
        value_str = get_custom_label_or_count(filter_rule, user_ids, "user")
        metadata_items = build_metadata_items(user_ids, "user")

        return FilterResult(
            field=api_field,
            value=value_str,
            operator=FilterOperator.Is,
            metadata=metadata_items,
        )


class DatasetFilterConverter(FilterConverter):
    """Handles Dataset filter conversion."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, list):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        dataset_ids = value
        value_str = get_custom_label_or_count(
            filter_rule, dataset_ids, "dataset"
        )
        metadata_items = build_metadata_items(dataset_ids, "dataset")

        return FilterResult(
            field=api_field,
            value=value_str,
            operator=FilterOperator.Is,
            metadata=metadata_items,
        )


class SampleFilterConverter(FilterConverter):
    """Handles Sample filter conversion."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, (int, float)):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        custom_label = filter_rule.get("__label")
        if custom_label:
            value_str = custom_label
        else:
            # Convert decimal back to percentage format for display
            percentage = int(value * 100)
            value_str = f"{percentage}%"

        return FilterResult(
            field=api_field,
            value=value_str,
            operator=FilterOperator.Is,
            metadata=value,  # Store the decimal value
        )


class AnnotationFilterConverter(FilterConverter):
    """Handles Annotation filter conversion."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, list):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        schema_node_ids = value
        value_str = get_custom_label_or_count(
            filter_rule, schema_node_ids, "annotation"
        )
        metadata_items = build_metadata_items(schema_node_ids, "annotation")

        return FilterResult(
            field=api_field,
            value=value_str,
            operator=FilterOperator.Is,
            metadata=metadata_items,
        )


class IssueCategoryFilterConverter(FilterConverter):
    """Handles IssueCategory filter conversion."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, list):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        issue_category_ids = value
        value_str = get_custom_label_or_count(
            filter_rule, issue_category_ids, "issue category"
        )
        metadata_items = build_metadata_items(issue_category_ids, "issue")

        return FilterResult(
            field=api_field,
            value=value_str,
            operator=FilterOperator.Is,
            metadata=metadata_items,
        )


class BatchFilterConverter(FilterConverter):
    """Handles Batch filter conversion."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, list):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        batch_ids = value

        # Extract operator from the filter rule (default to "is" for backward compatibility)
        operator = filter_rule.get("__operator", FilterOperator.Is)

        # Check if custom label was provided via __label field
        custom_label = filter_rule.get("__label")
        if custom_label:
            value_str = custom_label
        else:
            # Show count instead of placeholder names (original format)
            count = len(batch_ids)
            value_str = f"{count} batch{'es' if count != 1 else ''} selected"

        return FilterResult(
            field=api_field,
            value=value_str,
            operator=FilterOperator.Is,
            metadata={
                "filter": {
                    "ids": batch_ids,
                    "type": "batch",
                    "operator": operator,
                },
                "displayName": value_str,
                "searchQuery": {
                    "query": [
                        {
                            "ids": batch_ids,
                            "type": "batch",
                            "operator": operator,
                        }
                    ],
                    "scope": None,
                },
            },
        )


class TimeFilterConverter(FilterConverter):
    """Handles time-based filters (LabelingTime, ReviewTime)."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, dict):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        op, op_value = next(iter(value.items()))

        # Handle different operators
        if op == "less_than":
            display_value = f"< {format_time_duration(op_value)}"
            metadata_key = "time_lt"
            metadata_operator = "less_than"
        elif op == "less_than_or_equal":
            display_value = f"≤ {format_time_duration(op_value)}"
            metadata_key = "time_lte"
            metadata_operator = "less_than_or_equal"
        elif op == "greater_than":
            display_value = f"> {format_time_duration(op_value)}"
            metadata_key = "time_gt"
            metadata_operator = "greater_than"
        elif op == "greater_than_or_equal":
            display_value = f"≥ {format_time_duration(op_value)}"
            metadata_key = "time_gte"
            metadata_operator = "greater_than_or_equal"
        elif op in ["between_inclusive", "between_exclusive"]:
            return self._handle_time_range(api_field, op, op_value)
        else:
            # Fallback for unknown operators
            display_value = f"{op} {format_time_duration(op_value)}"
            metadata_key = f"time_{op}"
            metadata_operator = op

        return FilterResult(
            field=api_field,
            value=display_value,
            operator=FilterOperator.Is,
            metadata={
                metadata_key: op_value,
                "displayName": display_value,
                "operator": metadata_operator,
            },
        )

    def _handle_time_range(
        self, api_field: str, op: str, op_value: List[int]
    ) -> FilterResult:
        """Handle time range operations (between_inclusive, between_exclusive)."""
        start_val, end_val = op_value

        if op == "between_inclusive":
            # Inclusive uses square brackets notation like "[4h 59m, 5h]"
            display_value = f"[{format_time_duration(start_val)}, {format_time_duration(end_val)}]"
            metadata_key = "time_range_inclusive"
            metadata_operator = "between"  # API uses simple "between"
        else:
            # Exclusive uses parentheses notation like "(4h 59m, 5h)"
            display_value = f"({format_time_duration(start_val)}, {format_time_duration(end_val)})"
            metadata_key = "time_range_exclusive"
            metadata_operator = "between_exclusive"

        return FilterResult(
            field=api_field,
            value=display_value,
            operator=FilterOperator.Is,
            metadata={
                metadata_key: [start_val, end_val],
                "displayName": display_value,
                "operator": metadata_operator,
            },
        )


class ConsensusFilterConverter(FilterConverter):
    """Handles consensus-based filters."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if api_field == "ConsensusAverage":
            return self._handle_consensus_average(api_field, value)
        elif api_field == "FeatureConsensusAverage":
            return self._handle_feature_consensus_average(api_field, value)
        else:
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

    def _handle_consensus_average(
        self, api_field: str, value: Dict[str, Any]
    ) -> FilterResult:
        """Handle ConsensusAverage filter."""
        min_val = value.get("min", 0.0)
        max_val = value.get("max", 1.0)
        display_value = f"{int(min_val * 100)}% – {int(max_val * 100)}%"

        return FilterResult(
            field=api_field,
            value=display_value,
            operator=FilterOperator.Is,
            metadata=[min_val, max_val],  # Simple array format
        )

    def _handle_feature_consensus_average(
        self, api_field: str, value: Dict[str, Any]
    ) -> FilterResult:
        """Handle FeatureConsensusAverage filter."""
        min_val = value.get("min", 0.0)
        max_val = value.get("max", 1.0)
        annotations = value.get("annotations", [])

        # Build display value with percentage range and count
        percentage_range = f"{int(min_val * 100)}%–{int(max_val * 100)}%"

        if annotations:
            count = len(annotations)
            feature_count = (
                f"({count} feature{'s' if count != 1 else ''} selected)"
            )
            display_value = f"{percentage_range} {feature_count}"

            # Convert annotation IDs to full format for metadata
            if isinstance(annotations[0], str):
                # Simple ID list - convert to full format (placeholder names)
                annotation_objects = [
                    {"name": f"Feature {i+1}", "schemaNodeId": ann_id}
                    for i, ann_id in enumerate(annotations)
                ]
            else:
                # Already in full format
                annotation_objects = annotations
        else:
            display_value = percentage_range
            annotation_objects = []

        return FilterResult(
            field=api_field,
            value=display_value,
            operator=FilterOperator.Is,
            metadata={
                "min": min_val,
                "max": max_val,
                "annotations": annotation_objects,
            },
        )


class DateTimeFilterConverter(FilterConverter):
    """Handles LabeledAt date range filters."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, dict):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        op, op_value = next(iter(value.items()))
        if (
            op == "between"
            and isinstance(op_value, list)
            and len(op_value) == 2
        ):
            start_iso = op_value[0]
            end_iso = op_value[1]

            start_display = format_datetime_display(start_iso)
            end_display = format_datetime_display(end_iso)
            display_value = f"{start_display} – {end_display}"

            # Add .000Z suffix to ISO strings if not present for metadata
            start_metadata = (
                start_iso
                if ".000Z" in start_iso
                else start_iso.replace("Z", ".000Z")
            )
            end_metadata = (
                end_iso if ".000Z" in end_iso else end_iso.replace("Z", ".000Z")
            )

            return FilterResult(
                field=api_field,
                value=display_value,
                operator=FilterOperator.Is,
                metadata=[start_metadata, end_metadata],
            )

        return FilterResult(
            field=api_field,
            value="",
            operator=FilterOperator.Is,
        )


class NaturalLanguageFilterConverter(FilterConverter):
    """Handles NlSearch natural language filters."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, dict):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        content = value.get("content", "")
        score = value.get("score", {"min": 0.0, "max": 1.0})

        # Check if custom label was provided via __label field
        custom_label = filter_rule.get("__label")
        display_value = custom_label if custom_label else content

        return FilterResult(
            field=api_field,
            value=display_value,
            operator=FilterOperator.Is,
            metadata={
                "filter": {
                    "type": "nl_search",
                    "score": score,
                    "content": content,
                    "embedding": "CLIPV2",
                }
            },
        )


class ModelPredictionFilterConverter(FilterConverter):
    """Handles ModelPrediction filter conversion."""

    def convert(
        self, api_field: str, value: Any, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        if not isinstance(value, list):
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        prediction_conditions = value

        # Check if custom label was provided via __label field
        custom_label = filter_rule.get("__label")
        if custom_label:
            display_value = custom_label
        else:
            # Build display string (same pattern as metadata)
            display_parts = []

            for condition_item in prediction_conditions:
                operator = condition_item.get(
                    "type", ""
                )  # Changed from "operator" to "type"

                if operator == "is_none":
                    display_parts.append("is none")
                elif operator == "is_one_of":
                    models = condition_item.get("models", [])
                    min_score = condition_item.get("min_score", 0.0)
                    max_score = condition_item.get("max_score", 1.0)
                    models_str = ", ".join(models)
                    display_parts.append(
                        f"is one of {models_str} [{min_score} - {max_score}]"
                    )
                elif operator == "is_not_one_of":
                    models = condition_item.get("models", [])
                    min_score = condition_item.get("min_score", 0.0)
                    max_score = condition_item.get("max_score", 1.0)
                    models_str = ", ".join(models)
                    display_parts.append(
                        f"is not one of {models_str} [{min_score} - {max_score}]"
                    )

            # Join display parts with AND (same as metadata)
            display_value = " AND ".join(display_parts)

        # Build complex prediction structure with filters, displayName, searchQuery
        filters_array = []
        search_query_array = []

        for condition_item in prediction_conditions:
            operator = condition_item.get(
                "type", ""
            )  # Changed from "operator" to "type"

            if operator == "is_none":
                filters_array.append(
                    {
                        "type": "prediction",
                        "value": {"type": "prediction_does_not_exist"},
                    }
                )
                search_query_array.append({"type": "prediction_does_not_exist"})
            elif operator == "is_one_of":
                models = condition_item.get("models", [])
                min_score = condition_item.get("min_score", 0.0)
                max_score = condition_item.get("max_score", 1.0)

                # Build values array for this condition
                values_array = []
                for model_id in models:
                    # Generate proper UUID for valueId
                    value_id = str(uuid.uuid4())

                    # Build countRange - only include max if it's different from min
                    if min_score == max_score:
                        count_range = {"min": min_score}
                    else:
                        count_range = {"min": min_score, "max": max_score}

                    values_array.append(
                        {
                            "ids": [model_id],
                            "type": "schema_match_value",
                            "valueId": value_id,
                            "countRange": count_range,
                        }
                    )

                filters_array.append(
                    {
                        "type": "prediction",
                        "value": {
                            "type": "prediction_is",
                            "values": values_array,
                            "operator": "is",
                        },
                    }
                )

                # Search query structure for is_one_of
                search_values_array = []
                for model_id in models:
                    if min_score == max_score:
                        count_range = {"min": min_score}
                    else:
                        count_range = {"min": min_score, "max": max_score}

                    search_values_array.append(
                        {
                            "type": "schema_match_value",
                            "schemaId": model_id,
                            "countRange": count_range,
                        }
                    )

                search_query_array.append(
                    {
                        "type": "prediction",
                        "values": search_values_array,  # type: ignore[dict-item]
                        "operator": "is",
                    }
                )

            elif operator == "is_not_one_of":
                models = condition_item.get("models", [])
                min_score = condition_item.get("min_score", 0.0)
                max_score = condition_item.get("max_score", 1.0)

                # Build values array for this condition
                values_array = []
                for model_id in models:
                    # Generate proper UUID for valueId
                    value_id = str(uuid.uuid4())

                    # Build countRange - only include max if it's different from min
                    if min_score == max_score:
                        count_range = {"min": min_score}
                    else:
                        count_range = {"min": min_score, "max": max_score}

                    values_array.append(
                        {
                            "ids": [model_id],
                            "type": "schema_match_value",
                            "valueId": value_id,
                            "countRange": count_range,
                        }
                    )

                filters_array.append(
                    {
                        "type": "prediction",
                        "value": {
                            "type": "prediction_is",
                            "values": values_array,
                            "operator": "is_not",
                        },
                    }
                )

                # Search query structure for is_not_one_of
                search_values_array = []
                for model_id in models:
                    if min_score == max_score:
                        count_range = {"min": min_score}
                    else:
                        count_range = {"min": min_score, "max": max_score}

                    search_values_array.append(
                        {
                            "type": "schema_match_value",
                            "schemaId": model_id,
                            "countRange": count_range,
                        }
                    )

                search_query_array.append(
                    {
                        "type": "prediction",
                        "values": search_values_array,  # type: ignore[dict-item]
                        "operator": "is_not",
                    }
                )

        return FilterResult(
            field=api_field,
            value=display_value,
            operator=FilterOperator.Is,
            metadata={
                "filters": filters_array,
                "displayName": display_value,
                "searchQuery": {
                    "query": search_query_array,
                    "scope": {
                        "projectId": "placeholder_project_id"  # This should be filled by the actual project
                    },
                },
            },
        )


class FilterAPIConverter:
    """Main converter class that orchestrates all filter conversions."""

    def __init__(self):
        """Initialize converter with all available filter converters."""
        self.converters = {
            "CreatedBy": CreatedByFilterConverter(),
            "Dataset": DatasetFilterConverter(),
            "Sample": SampleFilterConverter(),
            "Annotation": AnnotationFilterConverter(),
            "IssueCategory": IssueCategoryFilterConverter(),
            "Batch": BatchFilterConverter(),
            "LabelingTime": TimeFilterConverter(),
            "ReviewTime": TimeFilterConverter(),
            "ConsensusAverage": ConsensusFilterConverter(),
            "FeatureConsensusAverage": ConsensusFilterConverter(),
            "LabeledAt": DateTimeFilterConverter(),
            "NlSearch": NaturalLanguageFilterConverter(),
            "ModelPrediction": ModelPredictionFilterConverter(),
        }

    def convert_to_api_format(
        self, filter_rule: Dict[str, Any]
    ) -> FilterResult:
        """
        Convert filter function output directly to API format.

        This is the refactored version of the original massive convert_to_api_format function.

        Args:
            filter_rule: Filter rule dictionary from filter functions

        Returns:
            API-formatted filter dictionary
        """
        if not filter_rule:
            return FilterResult(
                field="",
                value="",
                operator=FilterOperator.Is,
            )

        for key, value in filter_rule.items():
            # Skip internal fields
            if key.startswith("__"):
                continue

            # Handle manual metadata filters by capitalizing the field name
            api_field = "Metadata" if key == "metadata" else key

            # Get the appropriate converter
            converter = self.converters.get(api_field)
            if converter:
                return converter.convert(api_field, value, filter_rule)

            # Handle special cases not covered by converters yet
            if api_field == "Metadata":
                return self._handle_metadata_filter(
                    api_field, value, filter_rule
                )
            elif api_field == "ModelPrediction":
                return self._handle_model_prediction_filter(
                    api_field, value, filter_rule
                )

            # Default fallback
            return FilterResult(
                field=api_field,
                value=str(value) if value is not None else "",
                operator=FilterOperator.Is,
            )

        # Fallback if no keys found
        return FilterResult(
            field="",
            value="",
            operator=FilterOperator.Is,
        )

    def _handle_metadata_filter(
        self,
        api_field: str,
        value: List[Dict[str, Any]],
        filter_rule: Dict[str, Any],
    ) -> FilterResult:
        """Handle complex metadata filters."""
        if not isinstance(value, list) or not value:
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        # Check for custom label
        custom_label = filter_rule.get("__label")
        if custom_label:
            value_str = custom_label
        else:
            # Show count instead of placeholder names
            count = len(value)
            value_str = f"{count} metadata condition{'s' if count != 1 else ''} selected"

        # Build complex metadata structure (regardless of custom label)
        filters_array = []
        search_query_array = []

        for filter_item in value:
            meta_key = filter_item.get("key", "")
            meta_operator = filter_item.get("operator", "equals")
            meta_value = filter_item.get("value", "")

            # Format display part
            display_op, json_operator = format_metadata_operator(meta_operator)

            # Handle different value types (string vs list)
            if isinstance(meta_value, list):
                # Ensure all values are strings for the helper functions
                string_values_array = [str(v) for v in meta_value]
            else:
                # Ensure single value is in a list of strings
                string_values_array = [str(meta_value)]

            # Create filters array entry with correct structure
            filters_array.append(
                {
                    "type": "metadata",
                    "field": {
                        "type": "stringArray",
                        "value": {
                            "type": "stringArray",
                            "values": string_values_array,
                            "operator": json_operator,
                        },
                        "schemaId": meta_key,  # Use key as schemaId
                    },
                }
            )

            # Create search query entry with correct structure
            search_query_array.append(
                {
                    "type": "metadata",
                    "value": {
                        "type": "string",
                        "values": string_values_array,
                        "operator": json_operator,
                        "schemaId": meta_key,  # Use key as schemaId
                    },
                }
            )

        return FilterResult(
            field=api_field,
            value=value_str,
            operator=FilterOperator.Is,
            metadata={
                "filters": filters_array,
                "displayName": value_str,
                "searchQuery": {
                    "query": search_query_array,
                    "scope": {
                        "projectId": "placeholder_project_id"  # This should be filled by the actual project
                    },
                },
            },
        )

    def _handle_model_prediction_filter(
        self,
        api_field: str,
        value: List[Dict[str, Any]],
        filter_rule: Dict[str, Any],
    ) -> FilterResult:
        """Handle complex model prediction filters."""
        if not isinstance(value, list) or not value:
            return FilterResult(
                field=api_field,
                value="",
                operator=FilterOperator.Is,
            )

        # Check for custom label
        custom_label = filter_rule.get("__label")
        if custom_label:
            display_value = custom_label
        else:
            # Generate display based on condition types with actual model names
            condition_descriptions = []
            for condition in value:
                if isinstance(condition, dict):
                    condition_type = condition.get("type", "")
                    if condition_type == "is_none":
                        condition_descriptions.append("is none")
                    elif condition_type == "is_one_of":
                        models = condition.get("models", [])
                        # Use actual model names as expected by tests
                        model_names = ", ".join(models)
                        condition_descriptions.append(
                            f"is one of {model_names}"
                        )
                    elif condition_type == "is_not_one_of":
                        models = condition.get("models", [])
                        # Use actual model names as expected by tests
                        model_names = ", ".join(models)
                        condition_descriptions.append(
                            f"is not one of {model_names}"
                        )

            if condition_descriptions:
                # Join multiple conditions with " AND " as expected by tests
                display_value = " AND ".join(condition_descriptions)
            else:
                count = len(value)
                display_value = f"{count} model prediction condition{'s' if count != 1 else ''} selected"

        return FilterResult(
            field=api_field,
            value=display_value,
            operator=FilterOperator.Is,
            metadata=value,  # Store original conditions
        )
