from enum import Enum


class BulkImportRequestState(Enum):
    """ State of the import job when importing annotations (RUNNING, FAILED, or FINISHED).

       If you are not usinig MEA continue using BulkImportRequest.
       AnnotationImports are in beta and will change soon.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - RUNNING
         - Indicates that the import job is not done yet.
       * - FAILED
         - Indicates the import job failed. Check `BulkImportRequest.errors` for more information
       * - FINISHED
         - Indicates the import job is no longer running. Check `BulkImportRequest.statuses` for more information
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


class CollectionJobStatus(Enum):
    """ Status of an asynchronous job over a collection.

        * - State
          - Description
        * - SUCCESS
          - Indicates job has successfully processed entire collection of data
        * - PARTIAL SUCCESS
          - Indicates some data in the collection has succeeded and other data have failed
        * - FAILURE
          - Indicates job has failed to process entire collection of data
    """
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL SUCCESS"
    FAILURE = "FAILURE"