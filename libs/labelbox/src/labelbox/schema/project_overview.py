from typing import Dict, Optional
from labelbox import pydantic_compat

class Project_Overview(pydantic_compat.BaseModel):
    """
    Class that represents a project overview.
    """
    to_label: int
    in_review: Dict[str, int]
    in_rework: int
    skipped: int
    done: int
    issues: int
    labeled: int
    all_in_data_rows: int