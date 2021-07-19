from pydantic import BaseModel


class Metric(BaseModel):
    metric_value: float
