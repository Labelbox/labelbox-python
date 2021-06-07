from enum import Enum
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field

class AssetAttachment(DbObject):
    """ Asset attachment provides extra context about an asset while labeling.

    Attributes:
        attachment_type (str): IMAGE, VIDEO, TEXT, or IMAGE_OVERLAY
        attachment_value (str): URL to an external file or a string of text
    """

    class MetaType(Enum):
        VIDEO = "VIDEO"
        IMAGE = "IMAGE"
        TEXT = "TEXT"
        IMAGE_OVERLAY = "IMAGE_OVERLAY"

    # For backwards compatibility
    for topic in MetaType:
        vars()[topic.name] = topic.value


    attachment_type = Field.String("attachment_type")
    attachment_value = Field.String("attachment_value")
