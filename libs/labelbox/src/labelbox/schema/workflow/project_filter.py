"""Project workflow filters for Labelbox with functional filter construction API."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from labelbox.utils import title_case
from datetime import datetime


class DateTimeField:
    """Field class for datetime fields like labeled_at that supports method chaining."""

    def __init__(self, field_name: str):
        # Convert snake_case to PascalCase for backend field names
        self._field_name = title_case(field_name)

    def between(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Create a between filter for datetime fields.

        Args:
            start: Start datetime
            end: End datetime

        Returns:
            Dict representing the filter rule

        Example:
            from datetime import datetime
            labeled_at.between(
                datetime(2024, 1, 1),
                datetime(2024, 12, 31)
            )
        """
        # Convert datetime objects to ISO strings with Z suffix
        start_str = start.isoformat() + "Z"
        end_str = end.isoformat() + "Z"
        return {self._field_name: {"between": [start_str, end_str]}}


class TimeField:
    """Field class for time duration fields like labeling_time, review_time that supports method chaining."""

    def __init__(self, field_name: str):
        # Convert snake_case to PascalCase for backend field names
        self._field_name = title_case(field_name)

    def greater_than(self, seconds: int) -> Dict[str, Any]:
        """Filter for times greater than specified seconds.

        Args:
            seconds: Time threshold in seconds

        Example:
            labeling_time.greater_than(300)  # > 5 minutes
        """
        return {self._field_name: {"greater_than": seconds}}

    def less_than(self, seconds: int) -> Dict[str, Any]:
        """Filter for times less than specified seconds."""
        return {self._field_name: {"less_than": seconds}}

    def greater_than_or_equal(self, seconds: int) -> Dict[str, Any]:
        """Filter for times greater than or equal to specified seconds."""
        return {self._field_name: {"greater_than_or_equal": seconds}}

    def less_than_or_equal(self, seconds: int) -> Dict[str, Any]:
        """Filter for times less than or equal to specified seconds."""
        return {self._field_name: {"less_than_or_equal": seconds}}

    def between(
        self, start: int, end: int, inclusive: bool = True
    ) -> Dict[str, Any]:
        """Filter for times between start and end values.

        Args:
            start: Start time in seconds
            end: End time in seconds
            inclusive: Whether the range is inclusive (default: True)

        Example:
            labeling_time.between(300, 1800)  # 5 minutes to 30 minutes
        """
        operator = "between_inclusive" if inclusive else "between_exclusive"
        return {self._field_name: {operator: [start, end]}}


# Field instances for chaining syntax
labeled_at = DateTimeField("labeled_at")
labeling_time = TimeField("labeling_time")
review_time = TimeField("review_time")


class ListField:
    """Field class for list-based filters like batch, dataset that support is_one_of methods."""

    def __init__(self, field_name: str):
        self._field_name = field_name

    def is_one_of(self, values: List[str]) -> Dict[str, Any]:
        """Filter for items that are one of the specified values.

        Args:
            values: List of IDs to match
        """
        return {self._field_name: values}

    def is_not_one_of(self, values: List[str]) -> Dict[str, Any]:
        """Filter for items that are NOT one of the specified values.

        Args:
            values: List of IDs to exclude
        """
        return {self._field_name: values, "__operator": "is_not"}


class RangeField:
    """Field class for range-based filters like consensus_average."""

    def __init__(self, field_name: str):
        self._field_name = field_name

    def __call__(self, min: float, max: float) -> Dict[str, Any]:
        """Create a range filter.

        Args:
            min: Minimum value (0.0 to 1.0)
            max: Maximum value (0.0 to 1.0)
        """
        if not (0.0 <= min <= 1.0):
            raise ValueError(f"min must be between 0.0 and 1.0, got {min}")
        if not (0.0 <= max <= 1.0):
            raise ValueError(f"max must be between 0.0 and 1.0, got {max}")
        if min > max:
            raise ValueError(f"min ({min}) cannot be greater than max ({max})")

        return {self._field_name: {"min": min, "max": max}}


class FeatureRangeField:
    """Field class for feature-based range filters like feature_consensus_average."""

    def __init__(self, field_name: str):
        self._field_name = field_name

    def __call__(
        self, min: float, max: float, annotations: List[str]
    ) -> Dict[str, Any]:
        """Create a feature range filter.

        Args:
            min: Minimum value (0.0 to 1.0)
            max: Maximum value (0.0 to 1.0)
            annotations: List of annotation schema node IDs
        """
        if not (0.0 <= min <= 1.0):
            raise ValueError(f"min must be between 0.0 and 1.0, got {min}")
        if not (0.0 <= max <= 1.0):
            raise ValueError(f"max must be between 0.0 and 1.0, got {max}")
        if min > max:
            raise ValueError(f"min ({min}) cannot be greater than max ({max})")

        return {
            self._field_name: {
                "min": min,
                "max": max,
                "annotations": annotations,
            }
        }


# Additional field instances for chaining syntax
batch = ListField("Batch")
consensus_average = RangeField("ConsensusAverage")
feature_consensus_average = FeatureRangeField("FeatureConsensusAverage")

# List-based filter field instances
labeled_by = ListField("CreatedBy")  # Maps to backend CreatedBy field
dataset = ListField("Dataset")
issue_category = ListField("IssueCategory")
annotation = ListField("Annotation")


class MetadataCondition:
    """Helper class for building metadata conditions that can be combined."""

    @staticmethod
    def contains(key: str, value: str) -> Dict[str, str]:
        """Create a metadata contains condition."""
        return {"key": key, "operator": "contains", "value": value}

    @staticmethod
    def starts_with(key: str, value: str) -> Dict[str, str]:
        """Create a metadata starts_with condition."""
        return {"key": key, "operator": "starts_with", "value": value}

    @staticmethod
    def ends_with(key: str, value: str) -> Dict[str, str]:
        """Create a metadata ends_with condition."""
        return {"key": key, "operator": "ends_with", "value": value}

    @staticmethod
    def does_not_contain(key: str, value: str) -> Dict[str, str]:
        """Create a metadata does_not_contain condition."""
        return {"key": key, "operator": "does_not_contain", "value": value}

    @staticmethod
    def is_any(key: str, values: List[str]) -> Dict[str, Any]:
        """Create a metadata is_any condition."""
        return {"key": key, "operator": "is_any", "value": values}

    @staticmethod
    def is_not_any(key: str, values: List[str]) -> Dict[str, Any]:
        """Create a metadata is_not_any condition."""
        return {"key": key, "operator": "is_not_any", "value": values}

    @staticmethod
    def is_none() -> Dict[str, str]:
        """Create a model prediction is_none condition."""
        return {"operator": "is_none"}

    @staticmethod
    def is_one_of(
        models: List[str], min_score: float, max_score: float
    ) -> Dict[str, Any]:
        """Create a model prediction is_one_of condition.

        Args:
            models: List of model IDs
            min_score: Minimum score threshold (0.0 to 1.0)
            max_score: Maximum score threshold (0.0 to 1.0)

        Returns:
            Dict representing the condition
        """
        return {
            "type": "is_one_of",
            "models": models,
            "min_score": min_score,
            "max_score": max_score,
        }

    @staticmethod
    def is_not_one_of(
        models: List[str], min_score: float, max_score: float
    ) -> Dict[str, Any]:
        """Create a model prediction is_not_one_of condition.

        Args:
            models: List of model IDs
            min_score: Minimum score threshold (0.0 to 1.0)
            max_score: Maximum score threshold (0.0 to 1.0)

        Returns:
            Dict representing the condition
        """
        return {
            "type": "is_not_one_of",
            "models": models,
            "min_score": min_score,
            "max_score": max_score,
        }


def metadata(
    conditions: List[Dict[str, Any]], label: Optional[str] = None
) -> Dict[str, Any]:
    """Filter by metadata conditions.

    Args:
        conditions: List of metadata conditions created using MetadataCondition methods
        label: Optional custom label to display in the UI

    Returns:
        Dict representing the filter rule

    Example:
        metadata([
            MetadataCondition.contains("tag", "important"),
            MetadataCondition.starts_with("category", "prod")
        ])
    """
    result: Dict[str, Any] = {"Metadata": conditions}
    if label is not None:
        result["__label"] = label
    return result


def sample(percentage: int, label: Optional[str] = None) -> Dict[str, Any]:
    """Filter by random sample percentage.

    Args:
        percentage: Percentage of data to sample (1-100)
        label: Optional custom label to display in the UI

    Returns:
        Dict representing the filter rule

    Example:
        sample(20)  # 20% random sample
    """
    if not (1 <= percentage <= 100):
        raise ValueError(
            f"percentage must be between 1 and 100, got {percentage}"
        )

    # Convert percentage to decimal for API
    decimal_value = percentage / 100.0

    result: Dict[str, Any] = {"Sample": decimal_value}
    if label is not None:
        result["__label"] = label
    return result


def model_prediction(
    conditions: List[Dict[str, Any]], label: Optional[str] = None
) -> Dict[str, Any]:
    """Filter by model prediction conditions.

    Args:
        conditions: List of model prediction conditions created using MetadataCondition methods
        label: Optional custom label to display in the UI

    Returns:
        Dict representing the filter rule

    Example:
        model_prediction([
            MetadataCondition.is_one_of(["model-123"], 0.8, 1.0),
            MetadataCondition.is_none()
        ])
    """
    result: Dict[str, Any] = {"ModelPrediction": conditions}
    if label is not None:
        result["__label"] = label
    return result


def natural_language(
    content: str,
    min_score: float = 0.0,
    max_score: float = 1.0,
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """Filter by natural language semantic search.

    Args:
        content: Search query text
        min_score: Minimum similarity score (0.0 to 1.0)
        max_score: Maximum similarity score (0.0 to 1.0)
        label: Optional custom label to display in the UI

    Returns:
        Dict representing the filter rule

    Example:
        natural_language("cars and trucks", min_score=0.7)
    """
    if not (0.0 <= min_score <= 1.0):
        raise ValueError(
            f"min_score must be between 0.0 and 1.0, got {min_score}"
        )
    if not (0.0 <= max_score <= 1.0):
        raise ValueError(
            f"max_score must be between 0.0 and 1.0, got {max_score}"
        )
    if min_score > max_score:
        raise ValueError(
            f"min_score ({min_score}) cannot be greater than max_score ({max_score})"
        )

    result: Dict[str, Any] = {
        "NlSearch": {
            "content": content,
            "score": {"min": min_score, "max": max_score},
        }
    }
    if label is not None:
        result["__label"] = label
    return result


# Legacy helper functions for backward compatibility
def metadata_filter(key: str, operator: str, value: str) -> Dict[str, Any]:
    """Legacy metadata filter function.

    Args:
        key: Metadata key
        operator: Filter operator
        value: Filter value

    Returns:
        Dict representing the metadata filter rule
    """
    return metadata([{"key": key, "operator": operator, "value": value}])


def metadata_contains(key: str, value: str) -> Dict[str, Any]:
    """Legacy metadata contains filter function."""
    return metadata([MetadataCondition.contains(key, value)])


def metadata_starts_with(key: str, value: str) -> Dict[str, Any]:
    """Legacy metadata starts_with filter function."""
    return metadata([MetadataCondition.starts_with(key, value)])


def metadata_ends_with(key: str, value: str) -> Dict[str, Any]:
    """Legacy metadata ends_with filter function."""
    return metadata([MetadataCondition.ends_with(key, value)])


def create_metadata_filter_entry(
    meta_key: str, json_operator: str, values_array: List[str], filter_id: str
) -> Dict[str, Any]:
    """Create a metadata filter entry for API format."""
    return {
        "type": "metadata",
        "value": {
            "type": "metadata_search_value",
            "operator": json_operator,
            "values": [
                {"key": meta_key, "value": value} for value in values_array
            ],
        },
        "filterId": filter_id,
    }


def create_search_query_entry(
    json_operator: str, values_array: List[str], meta_key: str, filter_id: str
) -> Dict[str, Any]:
    """Create a search query entry for API format."""
    return {
        "type": "search_query",
        "value": {
            "type": "search_query_value",
            "operator": json_operator,
            "values": [
                {"key": meta_key, "value": value} for value in values_array
            ],
        },
        "filterId": filter_id,
    }


def convert_to_api_format(filter_rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert filter function output directly to API format.

    This function has been moved to filter_converters.py to avoid circular imports.
    This is a compatibility wrapper.

    Args:
        filter_rule: Filter rule dictionary from filter functions

    Returns:
        API-formatted filter dictionary
    """
    # TODO: Resolve circular dependency to avoid local import
    from .filter_converters import FilterAPIConverter

    # Use the new refactored converter
    converter = FilterAPIConverter()
    filter_result = converter.convert_to_api_format(filter_rule)

    # Convert FilterResult to dictionary for backward compatibility
    result = {
        "field": filter_result.field,
        "value": filter_result.value,
        "operator": filter_result.operator,
    }

    if filter_result.metadata is not None:
        result["metadata"] = filter_result.metadata

    return result


class ProjectWorkflowFilter(BaseModel):
    """
    Project workflow filter collection that enforces filter syntax.

    Only accepts filters created using filter field objects and functions in this module.
    This ensures type safety, IDE support, and eliminates manual string construction errors.

    Example Usage:
        filters = ProjectWorkflowFilter([
            labeled_by.is_one_of(["user-123"]),
            dataset.is_one_of(["dataset-456"]),
            issue_category.is_one_of(["cat1", "cat2"]),
            annotation.is_one_of(["bbox", "segmentation"]),
            sample(20),
            labeled_at.between("2024-01-01", "2024-12-31"),
            metadata([condition.contains("tag", "test")]),
            consensus_average(min=0.31, max=0.77)
        ])

        # Use with LogicNode
        logic.set_filters(filters)

        # Or add individual filters
        logic.add_filter(labeled_by.is_one_of(["user-123"]))
    """

    rules: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    filters: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self, filters_list: Optional[List[Dict[str, Any]]] = None, **data
    ):
        super().__init__(**data)
        if filters_list:
            for rule in filters_list:
                if rule:  # Skip empty rules
                    self._validate_filter_structure(rule)
                    self._add_or_replace_filter(rule)

    def _get_filter_field(self, rule: Dict[str, Any]) -> str:
        """Extract the filter field name from a rule."""
        # Rule should have exactly one key which is the field name
        return list(rule.keys())[0]

    def _add_or_replace_filter(self, rule: Dict[str, Any]) -> None:
        """Add a new filter or replace existing filter of the same type."""
        field_name = self._get_filter_field(rule)

        # Find and remove any existing filter with the same field
        self.rules = [
            r for r in self.rules if self._get_filter_field(r) != field_name
        ]
        self.filters = [f for f in self.filters if f.get("field") != field_name]

        # Add the new filter
        api_filter = convert_to_api_format(rule)
        self.filters.append(api_filter)
        self.rules.append(rule)

    def _validate_filter_structure(self, rule: Dict[str, Any]) -> None:
        """
        Validate that the filter has valid structure.

        Args:
            rule: Filter rule to validate

        Raises:
            ValueError: If the filter structure is invalid
        """
        if not isinstance(rule, dict) or not rule:
            raise ValueError(
                "Filters must be created using filter functions. "
                "Use functions like labeled_by([...]), metadata([...]), labeled_at.between(...), etc."
            )

        # Basic structural validation - ensure we have at least one field
        if len(rule.keys()) == 0:
            raise ValueError("Filter rule must contain at least one field")

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert all filter rules to API-ready format."""
        return self.filters.copy() if self.filters else []

    def append(self, rule: Dict[str, Any]) -> None:
        """Add a new filter rule, replacing any existing filter of the same type."""
        if rule:  # Skip empty rules
            self._validate_filter_structure(rule)
            self._add_or_replace_filter(rule)

    def get_filter_logic(self) -> str:
        """Get the default filter logic for these filters."""
        if not self.filters:
            return ""
        # Default is to AND all filters
        indices = list(range(len(self.filters)))
        return " AND ".join(str(i) for i in indices)

    def clear(self) -> None:
        """Clear all filter rules and normalized filters."""
        self.rules = []
        self.filters = []

    def __len__(self) -> int:
        """Return the number of filters."""
        return len(self.filters)

    def __bool__(self) -> bool:
        """Return True if there are filters."""
        return bool(self.filters)


class ModelPredictionCondition:
    """Helper class for building model prediction conditions."""

    @staticmethod
    def is_none() -> Dict[str, str]:
        """Create a condition for data rows with no model predictions."""
        return {"type": "is_none"}

    @staticmethod
    def is_one_of(
        models: List[str], min_score: float, max_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a condition for data rows where model predictions are in the specified list.

        Args:
            models: List of model names/IDs to match
            min_score: Minimum prediction score (0.0 to 1.0). If max_score is None, this is used as both min and max.
            max_score: Optional maximum score. If not provided, min_score is used as both min and max.

        Returns:
            Dict representing the condition
        """
        if max_score is None:
            # Single score mode (as used in reference code): score becomes both min and max
            max_score = min_score

        return {
            "type": "is_one_of",
            "models": models,
            "min_score": min_score,
            "max_score": max_score,
        }

    @staticmethod
    def is_not_one_of(
        models: List[str], min_score: float, max_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a condition for data rows where model predictions are NOT in the specified list.

        Args:
            models: List of model names/IDs to exclude
            min_score: Minimum prediction score (0.0 to 1.0). If max_score is None, this is used as both min and max.
            max_score: Optional maximum score. If not provided, min_score is used as both min and max.

        Returns:
            Dict representing the condition
        """
        if max_score is None:
            # Single score mode (as used in reference code): score becomes both min and max
            max_score = min_score

        return {
            "type": "is_not_one_of",
            "models": models,
            "min_score": min_score,
            "max_score": max_score,
        }


# Convenient aliases
m_condition: MetadataCondition = MetadataCondition()
mp_condition = ModelPredictionCondition
