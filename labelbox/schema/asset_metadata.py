from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class AssetMetadata(DbObject):
    """ Asset metadata (AKA Attachments) provides extra context about an asset while labeling.

    Attributes:
        meta_type (str): IMAGE, VIDEO, TEXT, or IMAGE_OVERLAY
        meta_value (str): URL to an external file or a string of text
    """
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    TEXT = "TEXT"

    meta_type = Field.String("meta_type")
    meta_value = Field.String("meta_value")
