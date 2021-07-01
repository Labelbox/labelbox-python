from typing import Optional
import marshmallow_dataclass
from labelbox.data.annotation_types.annotation import (
    Annotation,
)
from labelbox.data.annotation_types.marshmallow import default_none, required


@marshmallow_dataclass.dataclass
class Metric(Annotation):
    metric_value: float = required()
    schema_id: Optional[float] = default_none()
