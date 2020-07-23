from enum import Enum


class BulkImportRequestState(Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"
