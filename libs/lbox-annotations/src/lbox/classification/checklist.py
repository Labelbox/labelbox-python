from typing import List

from pydantic import BaseModel

from ..mixins import ConfidenceMixin
from .classification_answer import ClassificationAnswer


class Checklist(ConfidenceMixin, BaseModel):
    """A classification with many selected options allowed

    >>> Checklist(answer = [ClassificationAnswer(name = "cloudy")])

    """

    answer: List[ClassificationAnswer]
