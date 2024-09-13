from enum import Enum


class LabelingServiceStatus(Enum):
    Accepted = "ACCEPTED"
    Calibration = "CALIBRATION"
    Complete = "COMPLETE"
    Production = "PRODUCTION"
    Requested = "REQUESTED"
    SetUp = "SET_UP"
    Missing = None

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)

    @classmethod
    def _missing_(cls, value) -> "LabelingServiceStatus":
        """Handle missing null new task types
        Handle upper case names for compatibility with
        the GraphQL"""

        if value is None:
            return cls.Missing

        for name, member in cls.__members__.items():
            if value == name.upper():
                return member

        return cls.Missing
