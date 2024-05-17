from typing import Dict, Optional
from labelbox import pydantic_compat

class ProjectOverview(pydantic_compat.BaseModel):
    """
    Class that represents a project overview as displayed in the UI
    All attributes represent the number of data rows in the corresponding state.
    The `in_review` attribute is a dictionary where the keys are the queue names
      and the values are the number of data rows in that queue.
    """
    to_label: int
    in_review: Dict[str, int]
    in_rework: int
    skipped: int
    done: int
    issues: int
    labeled: int
    all_in_data_rows: int