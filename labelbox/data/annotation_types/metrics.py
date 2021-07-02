from typing import Optional
import marshmallow_dataclass
from labelbox.data.annotation_types.annotation import (
    Annotation,
)
import uuid
from labelbox.data.annotation_types.marshmallow import default_none, required


@marshmallow_dataclass.dataclass
class Metric:
    metric_value: float = required()
    schema_id: Optional[float] = default_none()
    name: Optional[float] = default_none()

    def to_mal_ndjson(self):
        return {
            "metricValue" : self.metric_value,
            "uuid" : str(uuid.uuid4()),
        }
