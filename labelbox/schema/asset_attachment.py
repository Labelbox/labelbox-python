import warnings
from enum import Enum
from typing import Dict, Optional

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class AttachmentType(str, Enum):

    @classmethod
    def __missing__(cls, value: object):
        if str(value) == "TEXT":
            warnings.warn(
                "The TEXT attachment type is deprecated. Use RAW_TEXT instead.")
            return cls.RAW_TEXT
        return value

    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    IMAGE_OVERLAY = "IMAGE_OVERLAY"
    HTML = "HTML"
    RAW_TEXT = "RAW_TEXT"
    TEXT_URL = "TEXT_URL"
    PDF_URL = "PDF_URL"
    CAMERA_IMAGE = "CAMERA_IMAGE"  # Used by experimental point-cloud editor


class AssetAttachment(DbObject):
    """Asset attachment provides extra context about an asset while labeling.

    Attributes:
        attachment_type (str): IMAGE, VIDEO, IMAGE_OVERLAY, HTML, RAW_TEXT, TEXT_URL, or PDF_URL. TEXT attachment type is deprecated.
        attachment_value (str): URL to an external file or a string of text
        attachment_name (str): The name of the attachment
    """

    for topic in AttachmentType:
        vars()[topic.name] = topic.value

    attachment_type = Field.String("attachment_type", "type")
    attachment_value = Field.String("attachment_value", "value")
    attachment_name = Field.String("attachment_name", "name")

    @classmethod
    def validate_attachment_json(cls, attachment_json: Dict[str, str]) -> None:
        for required_key in ['type', 'value']:
            if required_key not in attachment_json:
                raise ValueError(
                    f"Must provide a `{required_key}` key for each attachment. Found {attachment_json}."
                )
        cls.validate_attachment_value(attachment_json['value'])
        cls.validate_attachment_type(attachment_json['type'])

    @classmethod
    def validate_attachment_value(cls, attachment_value: str) -> None:
        if not isinstance(attachment_value, str) or attachment_value == "":
            raise ValueError(
                f"Attachment value must be a non-empty string, got: '{attachment_value}'"
            )

    @classmethod
    def validate_attachment_type(cls, attachment_type: str) -> None:
        valid_types = set(AttachmentType.__members__)
        if attachment_type not in valid_types:
            raise ValueError(
                f"attachment_type must be one of {valid_types}. Found {attachment_type}"
            )

    def delete(self) -> None:
        """Deletes an attachment on the data row."""
        query_str = """mutation deleteDataRowAttachmentPyApi($attachment_id: ID!) {
            deleteDataRowAttachment(where: {id: $attachment_id}) {
                    id}
            }"""
        self.client.execute(query_str, {"attachment_id": self.uid})

    def update(self,
               name: Optional[str] = None,
               type: Optional[str] = None,
               value: Optional[str] = None):
        """Updates an attachment on the data row."""
        if not name and not type and value is None:
            raise ValueError(
                "At least one of the following must be provided: name, type, value"
            )

        query_params = {"attachment_id": self.uid}
        if type:
            self.validate_attachment_type(type)
            query_params["type"] = type
        if value is not None:
            self.validate_attachment_value(value)
            query_params["value"] = value
        if name:
            query_params["name"] = name

        query_str = """mutation updateDataRowAttachmentPyApi($attachment_id: ID!, $name: String, $type: AttachmentType, $value: String) {
            updateDataRowAttachment(
              where: {id: $attachment_id}, 
              data: {name: $name, type: $type, value: $value}
            ) { id name type value }
            }"""
        res = (self.client.execute(query_str,
                                   query_params))['updateDataRowAttachment']

        self.attachment_name = res['name']
        self.attachment_value = res['value']
        self.attachment_type = res['type']
