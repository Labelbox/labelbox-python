from pydantic import BaseModel


class LabelScore(BaseModel):
    """
    A label score.

    Attributes:
        name (str)
        score (float)

    """

    name: str
    score: float
