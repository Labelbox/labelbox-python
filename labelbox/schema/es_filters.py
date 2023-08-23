import sys

from datetime import datetime, timezone
from typing import Collection, Dict, Tuple, List, Optional
from labelbox.typing_imports import Literal
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

SEARCH_LIMIT_PER_EXPORT_V2 = 2_000
ISO_8061_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def build_id_filters(
        ids: list,
        type_name: str,
        search_where_limit: int = SEARCH_LIMIT_PER_EXPORT_V2) -> dict:
    if not isinstance(ids, list):
        raise ValueError(f"{type_name} filter expects a list.")
    if len(ids) == 0:
        raise ValueError(f"{type_name} filter expects a non-empty list.")
    if len(ids) > search_where_limit:
        raise ValueError(
            f"{type_name} filter only supports a max of {search_where_limit} items."
        )
    return {"ids": ids, "operator": "is", "type": type_name}
