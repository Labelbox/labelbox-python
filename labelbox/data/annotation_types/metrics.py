import uuid
from marshmallow_dataclass import dataclass

from labelbox.data.annotation_types.marshmallow import RequiredFieldMixin, required


@dataclass
class Metric(RequiredFieldMixin):
    metric_value: float = required()

    def to_mal_ndjson(self):
        return {
            "metricValue" : self.metric_value,
            "uuid" : str(uuid.uuid4()),
        }
