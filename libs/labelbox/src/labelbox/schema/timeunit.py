from enum import Enum


class TimeUnit(Enum):
    """Enum representing time units with their values in seconds.

    Used for time-based operations such as setting validity periods for API keys.

    Attributes:
        SECOND (int): 1 second
        MINUTE (int): 60 seconds
        HOUR (int): 3600 seconds (60 minutes)
        DAY (int): 86400 seconds (24 hours)
        WEEK (int): 604800 seconds (7 days)
    """

    SECOND: int = 1
    MINUTE: int = 60
    HOUR: int = 60 * 60
    DAY: int = 24 * 60 * 60
    WEEK: int = 7 * 24 * 60 * 60
