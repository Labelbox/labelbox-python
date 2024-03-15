from enum import Enum


class ConflictResolutionStrategy(str, Enum):
    KeepExisting = "KEEP_EXISTING"
    OverrideWithAnnotations = "OVERRIDE_WITH_ANNOTATIONS"
    OverrideWithPredictions = "OVERRIDE_WITH_PREDICTIONS"

    @staticmethod
    def from_str(label: str) -> "ConflictResolutionStrategy":
        return ConflictResolutionStrategy[label]
