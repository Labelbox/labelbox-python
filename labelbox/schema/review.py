from enum import Enum, auto

from labelbox.orm.db_object import DbObject, Updateable, Deletable
from labelbox.orm.model import Field, Relationship


class Review(DbObject, Deletable, Updateable):
    """ Reviewing labeled data is a collaborative quality assurance technique.
    A Review object indicates the quality of the assigned Label. The aggregated
    review numbers can be obtained on a Project object. """

    class NetScore(Enum):
        Negative = auto()
        Zero = auto()
        Positive = auto()

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    score = Field.Float("score")

    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    project = Relationship.ToOne("Project", False)
    label = Relationship.ToOne("Label", False)
