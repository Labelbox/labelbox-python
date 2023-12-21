from enum import Enum


class IdType(str, Enum):
    """
    The type of id used to identify a data row.
    
    Currently supported types are:
        - DataRowId: The id assigned to a data row by Labelbox.
        - GlobalKey: The id assigned to a data row by the user.
    """
    DataRowId = "ID"
    GlobalKey = "GKEY"
