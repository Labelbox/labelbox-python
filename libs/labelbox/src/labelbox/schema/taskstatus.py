from enum import Enum


class TaskStatus(str, Enum):
    In_Progress = "IN_PROGRESS"
    Complete = "COMPLETE"
    Canceling = "CANCELLING"
    Canceled = "CANCELED"
    Failed = "FAILED"
    Unknown = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):
        """Handle missing or unknown task status values.

        If a task status value is not found in the enum, this method returns
        the Unknown status instead of raising an error.

        Args:
            value: The status value that doesn't match any enum member

        Returns:
            TaskStatus.Unknown: The default status for unrecognized values
        """
        return cls.Unknown
