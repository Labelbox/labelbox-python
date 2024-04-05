import sys

if sys.version_info >= (3, 9):
    from strenum import StrEnum

    class BaseStrEnum(StrEnum):
        pass
else:
    from enum import Enum

    class BaseStrEnum(str, Enum):
        pass


class IdType(BaseStrEnum):
    """
    The type of id used to identify a data row.
    
    Currently supported types are:
        - DataRowId: The id assigned to a data row by Labelbox.
        - GlobalKey: The id assigned to a data row by the user.
    """
    DataRowId = "ID"
    GlobalKey = "GKEY"
