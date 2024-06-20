from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class LabelScore(DbObject):
    """
    a label score

    Attributes
    name
    score

    """

    name = Field.String("name")
    data_row_count = Field.Float("score")

    def __init__(self, client, *args, **kwargs):
        super().__init__(client, *args, **kwargs)
