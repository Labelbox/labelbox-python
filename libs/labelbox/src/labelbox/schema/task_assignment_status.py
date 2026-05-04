from enum import Enum


class TaskAssignmentStatus(str, Enum):
    """Status filter for bulk data row assignment.

    FREE - only assign data rows that are currently unassigned.
    RESERVED - only assign data rows that are currently reserved by another user.
    """

    FREE = "FREE"
    RESERVED = "RESERVED"
