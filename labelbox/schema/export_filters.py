import sys

from typing import Optional
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Tuple


class ProjectExportFilters(TypedDict):
    label_created_at: Optional[Tuple[str, str]]
    last_activity_at: Optional[Tuple[str, str]]
