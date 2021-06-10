from enum import Enum


class BulkImportRequestState(Enum):
    """ State of the import job when importing annotations (RUNNING, FAILED, or FINISHED).

    This object is deprecated. Please use AnnotationImportState instead.
    """
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"


class AnnotationImportState(Enum):
    """ State of the import job when importing annotations (RUNNING, FAILED, or FINISHED).

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - RUNNING
         - Indicates that the import job is not done yet.
       * - FAILED
         - Indicates the import job failed. Check `AnnotationImport.errors` for more information
       * - FINISHED
         - Indicates the import job is no longer running. Check `AnnotationImport.statuses` for more information
    """
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"


class ImportType(Enum):
    MODEL_ERROR_ANALYSIS = "MODEL_ERROR_ANALYSIS"
    MODEL_ASSISTED_LABELING = "MODEL_ASSISTED_LABELING"
