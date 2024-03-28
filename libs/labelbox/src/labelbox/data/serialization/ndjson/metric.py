from typing import Optional, Union, Type

from labelbox.data.annotation_types.data import ImageData, TextData
from labelbox.data.serialization.ndjson.base import DataRow, NDJsonBase
from labelbox.data.annotation_types.metrics.scalar import (
    ScalarMetric, ScalarMetricAggregation, ScalarMetricValue,
    ScalarMetricConfidenceValue)
from labelbox.data.annotation_types.metrics.confusion_matrix import (
    ConfusionMatrixAggregation, ConfusionMatrixMetric,
    ConfusionMatrixMetricValue, ConfusionMatrixMetricConfidenceValue)


class BaseNDMetric(NDJsonBase):
    metric_value: float
    feature_name: Optional[str] = None
    subclass_name: Optional[str] = None

    class Config:
        use_enum_values = True

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        for field in ['featureName', 'subclassName']:
            if res[field] is None:
                res.pop(field)
        return res


class NDConfusionMatrixMetric(BaseNDMetric):
    metric_value: Union[ConfusionMatrixMetricValue,
                        ConfusionMatrixMetricConfidenceValue]
    metric_name: str
    aggregation: ConfusionMatrixAggregation

    def to_common(self) -> ConfusionMatrixMetric:
        return ConfusionMatrixMetric(value=self.metric_value,
                                     metric_name=self.metric_name,
                                     feature_name=self.feature_name,
                                     subclass_name=self.subclass_name,
                                     aggregation=self.aggregation,
                                     extra={'uuid': self.uuid})

    @classmethod
    def from_common(
            cls, metric: ConfusionMatrixMetric,
            data: Union[TextData, ImageData]) -> "NDConfusionMatrixMetric":
        return cls(uuid=metric.extra.get('uuid'),
                   metric_value=metric.value,
                   metric_name=metric.metric_name,
                   feature_name=metric.feature_name,
                   subclass_name=metric.subclass_name,
                   aggregation=metric.aggregation,
                   data_row=DataRow(id=data.uid, global_key=data.global_key))


class NDScalarMetric(BaseNDMetric):
    metric_value: Union[ScalarMetricValue, ScalarMetricConfidenceValue]
    metric_name: Optional[str]
    aggregation: ScalarMetricAggregation = ScalarMetricAggregation.ARITHMETIC_MEAN

    def to_common(self) -> ScalarMetric:
        return ScalarMetric(value=self.metric_value,
                            metric_name=self.metric_name,
                            feature_name=self.feature_name,
                            subclass_name=self.subclass_name,
                            aggregation=self.aggregation,
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
                   data_row=DataRow(id=data.uid, global_key=data.global_key))

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        # For backwards compatibility.
        if res['metricName'] is None:
            res.pop('metricName')
            res.pop('aggregation')
        return res


class NDMetricAnnotation:

    @classmethod
    def to_common(
        cls, annotation: Union[NDScalarMetric, NDConfusionMatrixMetric]
    ) -> Union[ScalarMetric, ConfusionMatrixMetric]:
        return annotation.to_common()

    @classmethod
    def from_common(
        cls, annotation: Union[ScalarMetric,
                               ConfusionMatrixMetric], data: Union[TextData,
                                                                   ImageData]
    ) -> Union[NDScalarMetric, NDConfusionMatrixMetric]:
        obj = cls.lookup_object(annotation)
        return obj.from_common(annotation, data)

    @staticmethod
    def lookup_object(
        annotation: Union[ScalarMetric, ConfusionMatrixMetric]
    ) -> Union[Type[NDScalarMetric], Type[NDConfusionMatrixMetric]]:
        result = {
            ScalarMetric: NDScalarMetric,
            ConfusionMatrixMetric: NDConfusionMatrixMetric,
        }.get(type(annotation))
        if result is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation)}`")
        return result
