import sys

from datetime import datetime
from typing import Collection, Dict, Tuple, List, Optional

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

MAX_DATA_ROW_IDS_PER_EXPORT_V2 = 2_000


class SharedExportFilters(TypedDict):
    label_created_at: Optional[Tuple[str, str]]
    """ Date range for labels created at
    Formatted "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss"
    Examples: 
    >>>   ["2000-01-01 00:00:00", "2050-01-01 00:00:00"]
    >>>   [None, "2050-01-01 00:00:00"]
    >>>   ["2000-01-01 00:00:00", None]
    """
    last_activity_at: Optional[Tuple[str, str]]
    """ Date range for last activity at
    Formatted "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss"
    Examples: 
    >>>   ["2000-01-01 00:00:00", "2050-01-01 00:00:00"]
    >>>   [None, "2050-01-01 00:00:00"]
    >>>   ["2000-01-01 00:00:00", None]
    """
    data_row_ids: Optional[List[str]]
    """ Datarow ids to export
    Only allows MAX_DATAROW_IDS_PER_EXPORT_V2 datarows
    Example:
    >>>   ["clgo3lyax0000veeezdbu3ws4", "clgo3lzjl0001veeer6y6z8zp", ...]
    """


class ProjectExportFilters(SharedExportFilters):
    pass


class DatasetExportFilters(SharedExportFilters):
    pass


def validate_datetime(string_date: str) -> bool:
    """helper function validate that datetime is as follows: YYYY-MM-DD for the export"""
    if string_date:
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                datetime.strptime(string_date, fmt)
                return True
            except ValueError:
                pass
        raise ValueError(f"""Incorrect format for: {string_date}.
        Format must be \"YYYY-MM-DD\" or \"YYYY-MM-DD hh:mm:ss\"""")
    return True


def build_filters(client, filters):
    search_query: List[Dict[str, Collection[str]]] = []
    timezone: Optional[str] = None

    def _get_timezone() -> str:
        timezone_query_str = """query CurrentUserPyApi { user { timezone } }"""
        tz_res = client.execute(timezone_query_str)
        return tz_res["user"]["timezone"] or "UTC"

    last_activity_at = filters.get("last_activity_at")
    if last_activity_at:
        if timezone is None:
            timezone = _get_timezone()
        start, end = last_activity_at
        if (start is not None and end is not None):
            [validate_datetime(date) for date in last_activity_at]
            search_query.append({
                "type": "data_row_last_activity_at",
                "value": {
                    "operator": "BETWEEN",
                    "timezone": timezone,
                    "value": {
                        "min": start,
                        "max": end
                    }
                }
            })
        elif (start is not None):
            validate_datetime(start)
            search_query.append({
                "type": "data_row_last_activity_at",
                "value": {
                    "operator": "GREATER_THAN_OR_EQUAL",
                    "timezone": timezone,
                    "value": start
                }
            })
        elif (end is not None):
            validate_datetime(end)
            search_query.append({
                "type": "data_row_last_activity_at",
                "value": {
                    "operator": "LESS_THAN_OR_EQUAL",
                    "timezone": timezone,
                    "value": end
                }
            })

    label_created_at = filters.get("label_created_at")
    if label_created_at:
        if timezone is None:
            timezone = _get_timezone()
        start, end = label_created_at
        if (start is not None and end is not None):
            [validate_datetime(date) for date in label_created_at]
            search_query.append({
                "type": "labeled_at",
                "value": {
                    "operator": "BETWEEN",
                    "value": {
                        "min": start,
                        "max": end
                    }
                }
            })
        elif (start is not None):
            validate_datetime(start)
            search_query.append({
                "type": "labeled_at",
                "value": {
                    "operator": "GREATER_THAN_OR_EQUAL",
                    "value": start
                }
            })
        elif (end is not None):
            validate_datetime(end)
            search_query.append({
                "type": "labeled_at",
                "value": {
                    "operator": "LESS_THAN_OR_EQUAL",
                    "value": end
                }
            })

    data_row_ids = filters.get("data_row_ids")
    if data_row_ids:
        if not isinstance(data_row_ids, list):
            raise ValueError("`data_row_ids` filter expects a list.")
        if len(data_row_ids) > MAX_DATA_ROW_IDS_PER_EXPORT_V2:
            raise ValueError(
                f"`data_row_ids` filter only supports a max of {MAX_DATA_ROW_IDS_PER_EXPORT_V2} items."
            )
        search_query.append({
            "ids": data_row_ids,
            "operator": "is",
            "type": "data_row_id"
        })

    return search_query