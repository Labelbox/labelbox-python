from typing import Optional, Union
from uuid import UUID
from marshmallow.decorators import validates_schema
from labelbox.data.annotation_types.marshmallow import default_uuid, default_none
from marshmallow_dataclass import dataclass
from marshmallow import ValidationError


@dataclass
class DataRowRef:
    external_id: Union[str, UUID] = default_uuid()
    uid: Optional[str] = default_none()

@dataclass
class FeatureSchemaRef:
    display_name: str = default_none()
    schema_id: str = default_none()

    @validates_schema
    def must_provide_one(self, data, **_) -> None:
        if not any([data.display_name, data.schema_id]):
            raise ValidationError("Must provide either the display_name or a schema_id to indicate the feature schema")
