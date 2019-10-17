from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class AssetMetadata(DbObject):
    """ AssetMetadata is a datatype to provide extra context about an asset
    while labeling.
    """
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    TEXT = "TEXT"

    meta_type = Field.String("meta_type")
    meta_value = Field.String("meta_value")
