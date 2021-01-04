from enum import Enum


class BulkImportRequestState(Enum):
    """ State of the import job when importing annotations (RUNNING, FAILED, or FINISHED).
    """
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"
