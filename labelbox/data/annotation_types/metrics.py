import uuid

from pydantic import BaseModel


class Metric(BaseModel):
    metric_value: float

    def to_mal_ndjson(self):
        return {
            "metricValue": self.metric_value,
            "uuid": str(uuid.uuid4()),
        }
