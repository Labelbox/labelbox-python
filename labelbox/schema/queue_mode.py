from enum import Enum


class QueueMode(str, Enum):
    Batch = "BATCH"
    Dataset = "DATA_SET"

    @classmethod
    def _missing_(cls, value):
        # Parses the deprecated "CATALOG" value back to QueueMode.Batch.
        if value == "CATALOG":
            return QueueMode.Batch
