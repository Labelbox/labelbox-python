from typing import Dict, Optional
from labelbox import pydantic_compat

from typing import Dict
import pydantic_compat

class ProjectOverview(pydantic_compat.BaseModel):
    """
    Class that represents a project summary as displayed in the UI, in Annotate, 
    under the "Overview" tab of a particular project.

    All attributes represent the number of data rows in the corresponding state.
    The `in_review` attribute is a dictionary where the keys are the queue names
    and the values are the number of data rows in that queue.

    Attributes:
        Representing existing fields from the Overview tag (UI names in parentheses):

        to_label (int): The number of data rows that are yet to be labeled (To Label).
        in_review (Dict[str, int]): A dictionary where the keys are the queue names .
            and the values are the number of data rows in that queue. (In Review)
        in_rework (int): The number of data rows that are in the Rework queue (In Rework).
        skipped (int): The number of data rows that have been skipped (Skipped).
        done (int): The number of data rows that have been marked as Done (Done).
        issues (int): The number of data rows with associated issues (Issues).
        
        Additional values:

        labeled (int): The number of data rows that have been labeled.
        all_in_data_rows (int): The total number of data rows in the project.
    """
    to_label: int   
    in_review: Dict[str, int]
    in_rework: int
    skipped: int
    done: int
    issues: int
    labeled: int
    all_in_data_rows: int