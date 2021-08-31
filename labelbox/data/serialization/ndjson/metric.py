from labelbox.data.annotation_types.metrics.scalar import CustomScalarMetric
from typing import Literal, Union

from fiftyone.core.collections import aggregation

from labelbox.data.annotation_types.data import ImageData, TextData
from labelbox.data.annotation_types.metrics import ScalarMetric
from labelbox.data.serialization.ndjson.base import NDJsonBase


class NDDataRowScalarMetric(NDJsonBase):
    metric_value: float

    def to_common(self) -> ScalarMetric:
        return ScalarMetric(value=self.metric_value, extra={'uuid': self.uuid})

    @classmethod
    def from_common(
            cls, metric: ScalarMetric,
            data: Union[TextData, ImageData]) -> "NDDataRowScalarMetric":
        return NDDataRowScalarMetric(uuid=metric.extra.get('uuid'),
                                     metric_value=metric.value,
                                     data_row={'id': data.uid})


class NDCustomScalarMetric(NDJsonBase):
    metric_name: float
    metric_value: float
    sublcass_name: float
    aggregation: Union[Literal["ARITHMETIC_MEAN"], Literal["GEOMETRIC_MEAN"],
                       Literal["HARMONIC_MEAN"], Literal["SUM"]]

    def to_common(self) -> CustomScalarMetric:
        return ScalarMetric(value=self.metric_value, extra={'uuid': self.uuid})

    @classmethod
    def from_common(cls, metric: ScalarMetric,
                    data: Union[TextData, ImageData]) -> "NDCustomScalarMetric":
        return NDCustomScalarMetric(uuid=metric.extra.get('uuid'),
                                    metric_value=metric.value,
                                    data_row={'id': data.uid})


class NDMetricAnnotation:

    @classmethod
    def to_common(cls, annotation: "NDMetricType") -> ScalarMetric:

        return annotation.to_common()

    @classmethod
    def from_common(cls, annotation: Union[ScalarMetric, CustomScalarMetric],
                    data: Union[TextData, ImageData]) -> "NDMetricType":
        return NDDataRowScalarMetric.from_common(annotation, data)

    @staticmethod
    def lookup_object(
            metric: Union[ScalarMetric, CustomScalarMetric]) -> "NDMetricType":
        result = {
            ScalarMetric: NDDataRowScalarMetric,
            CustomScalarMetric: NDCustomScalarMetric,
        }.get(type(metric))
        if result is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(metric)}`")
        return result


NDMetricType = Union[NDDataRowScalarMetric, NDCustomScalarMetric]
