import sys

from datetime import datetime, timezone
from typing import Collection, Dict, Tuple, List, Optional
from labelbox.typing_imports import Literal
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

MAX_DATA_ROW_IDS_PER_EXPORT_V2 = 2_000
ISO_8061_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class BaseExportFilters(TypedDict):
    data_row_ids: Optional[List[str]]
    """ Datarow ids to export
    Only allows MAX_DATAROW_IDS_PER_EXPORT_V2 datarows
    Example:
    >>>   ["clgo3lyax0000veeezdbu3ws4", "clgo3lzjl0001veeer6y6z8zp", ...]

    """
    
    global_keys: Optional[List[str]]
    """ Global keys to export
    Only allows MAX_DATAROW_IDS_PER_EXPORT_V2 datarows
    Example:
    >>>   ["key1", "key2", ...]
    """

class SharedExportFilters(BaseExportFilters):
    label_created_at: Optional[Tuple[str, str]]
    """ Date range for labels created at
    Formatted "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss"
    Examples: 
    >>>   ["2000-01-01 00:00:00", "2050-01-01 00:00:00"]
    >>>   [None, "2050-01-01 00:00:00"]
    >>>   ["2000-01-01 00:00:00", None]
    """
    last_activity_at: Optional[Tuple[str, str]]



class ProjectExportFilters(SharedExportFilters):
    batch_ids: Optional[List[str]]
    """ Batch ids to export
    Example:
    >>> ["clgo3lyax0000veeezdbu3ws4"]
    """
    workflow_status: Optional[Literal["ToLabel", "InReview", "InRework",
                                      "Done"]]
    """ Export data rows matching workflow status
    Example:
    >>> "InReview"
    """


class DatasetExportFilters(SharedExportFilters):
    pass


class DatarowExportFilters(BaseExportFilters):
    pass


def validate_datetime(datetime_str: str) -> bool:
    """helper function to validate that datetime's format: "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss" 
    or ISO 8061 format "YYYY-MM-DDThh:mm:ss±hhmm" (Example: "2023-05-23T14:30:00+0530")"""
    if datetime_str:
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", ISO_8061_FORMAT):
            try:
                datetime.strptime(datetime_str, fmt)
                return True
            except ValueError:
                pass
        raise ValueError(f"""Incorrect format for: {datetime_str}.
        Format must be \"YYYY-MM-DD\" or \"YYYY-MM-DD hh:mm:ss\" or ISO 8061 format \"YYYY-MM-DDThh:mm:ss±hhmm\""""
                        )
    return True


def convert_to_utc_if_iso8061(datetime_str: str, timezone_str: Optional[str]):
    """helper function to convert datetime to UTC if it is in ISO_8061_FORMAT and set timezone to UTC"""
    try:
        date_obj = datetime.strptime(datetime_str, ISO_8061_FORMAT)
        date_obj_utc = date_obj.replace(tzinfo=timezone.utc)
        datetime_str = date_obj_utc.strftime(ISO_8061_FORMAT)
        timezone_str = "UTC"
    except ValueError:
        pass
    return datetime_str, timezone_str


def build_filters(client, filters):
    search_query: List[Dict[str, Collection[str]]] = []
    timezone: Optional[str] = None

    def _get_timezone() -> str:
        timezone_query_str = """query CurrentUserPyApi { user { timezone } }"""
        tz_res = client.execute(timezone_query_str)
        return tz_res["user"]["timezone"] or "UTC"

    def _build_es_id_filters(ids: list, es_type_name: str, elastic_search_where_limit:int = MAX_DATA_ROW_IDS_PER_EXPORT_V2) -> str:
        if not isinstance(ids, list):
            raise ValueError(f"{es_type_name} filter expects a list.")
        if len(ids) > elastic_search_where_limit:
            raise ValueError(
                f"{es_type_name} filter only supports a max of {elastic_search_where_limit} items."
            )
        search_query.append({
            "ids": ids,
            "operator": "is",
            "type": es_type_name
        })

    last_activity_at = filters.get("last_activity_at")
    if last_activity_at:
        timezone = _get_timezone()
        start, end = last_activity_at
        if (start is not None and end is not None):
            [validate_datetime(date) for date in last_activity_at]
            start, timezone = convert_to_utc_if_iso8061(start, timezone)
            end, timezone = convert_to_utc_if_iso8061(end, timezone)
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
            start, timezone = convert_to_utc_if_iso8061(start, timezone)
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
            end, timezone = convert_to_utc_if_iso8061(end, timezone)
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
        timezone = _get_timezone()
        start, end = label_created_at
        if (start is not None and end is not None):
            [validate_datetime(date) for date in label_created_at]
            start, timezone = convert_to_utc_if_iso8061(start, timezone)
            end, timezone = convert_to_utc_if_iso8061(end, timezone)
            search_query.append({
                "type": "labeled_at",
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
            start, timezone = convert_to_utc_if_iso8061(start, timezone)
            search_query.append({
                "type": "labeled_at",
                "value": {
                    "operator": "GREATER_THAN_OR_EQUAL",
                    "timezone": timezone,
                    "value": start
                }
            })
        elif (end is not None):
            validate_datetime(end)
            end, timezone = convert_to_utc_if_iso8061(end, timezone)
            search_query.append({
                "type": "labeled_at",
                "value": {
                    "operator": "LESS_THAN_OR_EQUAL",
                    "timezone": timezone,
                    "value": end
                }
            })

    data_row_ids = filters.get("data_row_ids")
    if data_row_ids is not None:
        _build_es_id_filters(data_row_ids, "data_row_id")

    global_keys = filters.get("global_keys")
    if global_keys is not None:
        _build_es_id_filters(global_keys, "global_key")

    batch_ids = filters.get("batch_ids")
    if batch_ids is not None:
        _build_es_id_filters(batch_ids, "batch")

    workflow_status = filters.get("workflow_status")
    if workflow_status:
        if not isinstance(workflow_status, str):
            raise ValueError("`workflow_status` filter expects a string.")
        elif workflow_status not in ["ToLabel", "InReview", "InRework", "Done"]:
            raise ValueError(
                "`workflow_status` filter expects one of 'InReview', 'InRework', or 'Done'."
            )

        if workflow_status == "ToLabel":
            search_query.append({"type": "task_queue_not_exist"})
        else:
            search_query.append({
                "type": 'task_queue_status',
                "status": workflow_status
            })

    return search_query
