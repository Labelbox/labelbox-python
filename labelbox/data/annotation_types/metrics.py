from pydantic import BaseModel


class Metric(BaseModel):
    """ Class representing metrics """
    metric_value: float
