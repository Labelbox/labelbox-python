from enum import Enum
import logging

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field

logger = logging.getLogger(__name__)


class AssetMetadata(DbObject):
    """
        `AssetMetadata` is deprecated. Use `AssetAttachment` instead
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.warning(
            "`AssetMetadata` is deprecated. Use `AssetAttachment` instead.")

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
