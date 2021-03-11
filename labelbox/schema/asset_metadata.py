from enum import Enum

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class AssetMetadata(DbObject):
    """ Asset metadata (AKA Attachments) provides extra context about an asset while labeling.

    Attributes:
        meta_type (str): IMAGE, VIDEO, TEXT, or IMAGE_OVERLAY
        meta_value (str): URL to an external file or a string of text
    """

    class MetaType(Enum):
        VIDEO = "VIDEO"
        IMAGE = "IMAGE"
        TEXT = "TEXT"
        IMAGE_OVERLAY = "IMAGE_OVERLAY"

    # For backwards compatibility
    for topic in MetaType:
        vars()[topic.name] = topic.value

    meta_type = Field.String("meta_type")
    meta_value = Field.String("meta_value")
