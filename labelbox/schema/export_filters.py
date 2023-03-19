import sys

from typing import Optional
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Tuple


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


class ProjectExportFilters(SharedExportFilters):
    pass


class DatasetExportFilters(SharedExportFilters):
    pass
