from enum import Enum
from typing import Dict

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class AssetAttachment(DbObject):
    """ Asset attachment provides extra context about an asset while labeling.

    Attributes:
        attachment_type (str): IMAGE, VIDEO, TEXT, IMAGE_OVERLAY, or HTML
        attachment_value (str): URL to an external file or a string of text
    """

    class AttachmentType(Enum):
        VIDEO = "VIDEO"
        IMAGE = "IMAGE"
        TEXT = "TEXT"
        IMAGE_OVERLAY = "IMAGE_OVERLAY"
        HTML = "HTML"

    for topic in AttachmentType:
        vars()[topic.name] = topic.value

    attachment_type = Field.String("attachment_type", "type")
    attachment_value = Field.String("attachment_value", "value")

    @classmethod
    def validate_attachment_json(cls, attachment_json: Dict[str, str]) -> None:
        for required_key in ['type', 'value']:
            if required_key not in attachment_json:
                raise ValueError(
                    f"Must provide a `{required_key}` key for each attachment. Found {attachment_json}."
                )
            cls.validate_attachment_type(attachment_json['type'])

    @classmethod
    def validate_attachment_type(cls, attachment_type: str) -> None:
        valid_types = set(cls.AttachmentType.__members__)
        if attachment_type not in valid_types:
            raise ValueError(
                f"meta_type must be one of {valid_types}. Found {attachment_type}"
            )

    def delete(self) -> None:
        """Deletes an attachment on the data row."""
        query_str = """mutation deleteDataRowAttachmentPyApi($attachment_id: ID!) {
            deleteDataRowAttachment(where: {id: $attachment_id}) {
                    id}
            }"""
        self.client.execute(query_str, {"attachment_id": self.uid})
