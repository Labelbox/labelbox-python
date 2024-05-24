from typing import Dict, List
from labelbox.pydantic_compat import BaseModel
from typing_extensions import TypedDict

class ProjectOverview(BaseModel):
    """
    Class that represents a project summary as displayed in the UI, in Annotate, 
    under the "Overview" tab of a particular project.

    All attributes represent the number of data rows in the corresponding state.
    The `to_label` attribute represents the number of data rows that are yet to be labeled (To Label).
    The `in_review` attribute is a dictionary where the keys are the queue names and the values are the number of data rows in that queue (In Review).
    The `in_rework` attribute represents the number of data rows that are in the Rework queue (In Rework).
    The `skipped` attribute represents the number of data rows that have been skipped (Skipped).
    The `done` attribute represents the number of data rows that have been marked as Done (Done).
    The `issues` attribute represents the number of data rows with associated issues (Issues).

    The following don't appear in the UI
    The `labeled` attribute represents the number of data rows that have been labeled.
    The `total_data_rows` attribute represents the total number of data rows in the project.
    """
    to_label: int   
    in_review: int
    in_rework: int
    skipped: int
    done: int
    issues: int
    labeled: int
    total_data_rows: int


class _QueueDetail(TypedDict):
    """
    Class that represents the detailed information of the queues in the project overview.
    The `data` attribute is a list of dictionaries where the keys are the queue names 
    and the values are the number of data rows in that queue.
    """
    data: List[Dict[str, int]]
    total: int
    

class ProjectOverviewDetailed(BaseModel):
    """
    Class that represents a project summary as displayed in the UI, in Annotate, 
    under the "Overview" tab of a particular project.
    This class adds the list of task queues for the `in_review` and `in_rework` attributes.

    All attributes represent the number of data rows in the corresponding state.
    The `to_label` attribute represents the number of data rows that are yet to be labeled (To Label).
    The `in_review` attribute is a dictionary where the keys are (In Review):
        data: a list of dictionaries with the queue name and the number of data rows
        total: the total number of data rows in the In Review state
    The `in_rework` attribute is a dictionary where the keys are (In Rework):
        data: a list of dictionaries with the queue name and the number of data rows
        total: the total number of data rows in the In Rework state
    The `skipped` attribute represents the number of data rows that have been skipped (Skipped).
    The `done` attribute represents the number of data rows that have been marked as Done (Done).
    The `issues` attribute represents the number of data rows with associated issues (Issues).

    The following don't appear in the UI
    The `labeled` attribute represents the number of data rows that have been labeled.
    The `total_data_rows` attribute represents the total number of data rows in the project.
    """

    to_label: int   
    in_review: _QueueDetail
    in_rework: _QueueDetail
    skipped: int
    done: int
    issues: int
    labeled: int
    total_data_rows: int