"""Utility functions for filter operations."""

import random
import string
from datetime import datetime
from typing import Dict, List, Any


def format_time_duration(seconds: int) -> str:
    """Convert seconds to human-readable time format.

    Args:
        seconds: Time duration in seconds

    Returns:
        Human-readable time string (e.g., "1h 30m", "5m 30s", "45s")

    Examples:
        >>> format_time_duration(3600)
        '1h'
        >>> format_time_duration(90)
        '1m 30s'
        >>> format_time_duration(45)
        '45s'
    """
    if seconds >= 3600:  # >= 1 hour
        hours = seconds // 3600
        remaining_seconds = seconds % 3600
        if remaining_seconds == 0:
            return f"{hours}h"
        else:
            minutes = remaining_seconds // 60
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    elif seconds >= 60:  # >= 1 minute
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes}m"
        else:
            return f"{minutes}m {remaining_seconds}s"
    else:
        return f"{seconds}s"


def generate_filter_id() -> str:
    """
    Generate a random filter ID.

    Returns:
        Random 6-character string of lowercase letters and digits
    """
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def format_datetime_display(iso_string: str) -> str:
    """
    Convert ISO datetime string to DD/MM/YYYY, HH:MM:SS format for display.

    Args:
        iso_string: ISO format datetime string (e.g., "2024-04-12T19:03:01Z")

    Returns:
        Formatted datetime string for display
    """
    if iso_string.endswith("Z"):
        iso_string = iso_string[:-1] + "+00:00"
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y, %H:%M:%S")


def build_metadata_items(
    ids: List[str], item_type: str, key_field: str = "id"
) -> List[Dict[str, str]]:
    """
    Build metadata items for list-based filters.

    Args:
        ids: List of IDs
        item_type: Type of item (e.g., "user", "dataset")
        key_field: Field name for the ID (default: "id")

    Returns:
        List of metadata items with placeholder names
    """
    if item_type == "user":
        return [
            {key_field: item_id, "email": f"user{i+1}@example.com"}
            for i, item_id in enumerate(ids)
        ]
    elif item_type == "dataset":
        return [
            {key_field: item_id, "name": f"Dataset {i+1}"}
            for i, item_id in enumerate(ids)
        ]
    elif item_type == "annotation":
        return [
            {"name": f"Annotation {i+1}", "schemaNodeId": item_id}
            for i, item_id in enumerate(ids)
        ]
    elif item_type == "issue":
        return [
            {key_field: item_id, "name": f"Issue Category {i+1}"}
            for i, item_id in enumerate(ids)
        ]
    else:
        return [
            {key_field: item_id, "name": f"{item_type.title()} {i+1}"}
            for i, item_id in enumerate(ids)
        ]


def get_custom_label_or_count(
    filter_rule: Dict[str, Any], ids: List[str], item_type: str
) -> str:
    """
    Get custom label from filter rule or generate count-based label.

    Args:
        filter_rule: The filter rule dictionary
        ids: List of IDs
        item_type: Type of item for count display

    Returns:
        Display label string
    """
    custom_label = filter_rule.get("__label")
    if custom_label:
        return custom_label

    count = len(ids)
    if item_type == "issue category":
        return f"{count} issue categor{'ies' if count != 1 else 'y'} selected"
    else:
        return f"{count} {item_type}{'s' if count != 1 else ''} selected"
