from enum import Enum


class QueueMode(str, Enum):
    Batch = "CATALOG"
    Dataset = "DATA_SET"
