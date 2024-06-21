from labelbox import pydantic_compat


class LabelScore(pydantic_compat.BaseModel):
    """
    a label score

    Attributes
    name
    score

    """

    name: str
    score: float
