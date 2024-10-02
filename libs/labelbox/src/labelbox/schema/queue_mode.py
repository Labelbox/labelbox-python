from enum import Enum


class QueueMode(str, Enum):
    Batch = "BATCH"
    Dataset = "DATA_SET"
