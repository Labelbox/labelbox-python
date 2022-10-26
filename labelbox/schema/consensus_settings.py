from pydantic import BaseModel


class ConsensusSettings(BaseModel):
    """Container for holding consensus quality settings

    >>> ConsensusSettings(
    >>>    numberOfLabels = 2,
    >>>    coveragePercentage = 0.2
    >>>  )

    Args:
        numberOfLabels: Number of labels for consensus
        coveragePercentage: Percentage of data rows to be labeled more than once
    """

    numberOfLabels: int
    coveragePercentage: float
