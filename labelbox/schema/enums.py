from enum import Enum


class UploadedFileType(Enum):
    ASSET = "ASSET"
    PREDICTIONS = "PREDICTIONS"


class BulkImportRequestState(Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"
