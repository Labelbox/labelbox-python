from enum import Enum

import logging

logger = logging.getLogger(__name__)


class QueueMode(str, Enum):
    Batch = "BATCHES"
    Dataset = "DATA_SET"

    @classmethod
    def _missing_(cls, value):
        # Parses the deprecated "CATALOG" value back to QueueMode.Batch.
        if value == "CATALOG":
            return QueueMode.Batch
