from labelbox import pydantic_compat


class LabelScore(pydantic_compat.BaseModel):
    """
    A label score.

    Attributes:
        name (str)
        score (float)

    """

    name: str
    score: float
