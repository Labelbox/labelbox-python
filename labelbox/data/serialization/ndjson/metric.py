from labelbox.data.annotation_types.metrics.aggregations import MetricAggregation
from typing import Union, Optional

from labelbox.data.annotation_types.data import ImageData, TextData
from labelbox.data.annotation_types.metrics import ScalarMetric
from labelbox.data.serialization.ndjson.base import NDJsonBase


class NDScalarMetric(NDJsonBase):
    metric_value: float
    metric_name: Optional[str]
    feature_name: Optional[str] = None
    subclass_name: Optional[str] = None
    aggregation: MetricAggregation = MetricAggregation.ARITHMETIC_MEAN.value

    def to_common(self) -> ScalarMetric:
        return ScalarMetric(value=self.metric_value,
                            metric_name=self.metric_name,
                            feature_name=self.feature_name,
                            subclass_name=self.subclass_name,
                            aggregation=MetricAggregation[self.aggregation],
                            extra={'uuid': self.uuid})

    @classmethod
    def from_common(cls, metric: ScalarMetric,
                    data: Union[TextData, ImageData]) -> "NDScalarMetric":
        return cls(uuid=metric.extra.get('uuid'),
                   metric_value=metric.value,
                   metric_name=metric.metric_name,
                   feature_name=metric.feature_name,
                   subclass_name=metric.subclass_name,
                   aggregation=metric.aggregation.value,
                   data_row={'id': data.uid})

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        for field in ['featureName', 'subclassName']:
            if res[field] is None:
                res.pop(field)

        # For backwards compatibility.
        if res['metricName'] is None:
            res.pop('metricName')
            res.pop('aggregation')
        return res

    class Config:
        use_enum_values = True


class NDMetricAnnotation:

    @classmethod
    def to_common(cls, annotation: "NDScalarMetric") -> ScalarMetric:
        return annotation.to_common()

    @classmethod
    def from_common(cls, annotation: ScalarMetric,
                    data: Union[TextData, ImageData]) -> "NDScalarMetric":
        obj = cls.lookup_object(annotation)
        return obj.from_common(annotation, data)

    @staticmethod
    def lookup_object(metric: ScalarMetric) -> "NDScalarMetric":
        result = {
            ScalarMetric: NDScalarMetric,
        }.get(type(metric))
        if result is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(metric)}`")
        return result
