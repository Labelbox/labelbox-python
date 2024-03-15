from labelbox.utils import _CamelCaseMixin


class ConsensusSettings(_CamelCaseMixin):
    """Container for holding consensus quality settings

    >>> ConsensusSettings(
    >>>    number_of_labels = 2,
    >>>    coverage_percentage = 0.2
    >>>  )

    Args:
        number_of_labels: Number of labels for consensus
        coverage_percentage: Percentage of data rows to be labeled more than once
    """

    number_of_labels: int
    coverage_percentage: float
