from labelbox.data.annotation_types.data import TextData, RasterData
from labelbox.data.annotation_types.metrics import ScalarMetric
from labelbox.data.serialization.ndjson.base import NDJsonBase
from typing import Union


class NDDataRowScalarMetric(NDJsonBase):
    metric_value: float

    def to_common(self) -> ScalarMetric:
        return ScalarMetric(value=self.metric_value, extra={'uuid': self.uuid})

    @classmethod
    def from_common(
            cls, metric: ScalarMetric,
            data: Union[TextData, RasterData]) -> "NDDataRowScalarMetric":
        return NDDataRowScalarMetric(uuid=metric.extra.get('uuid'),
                                     metric_value=metric.value,
                                     data_row={'id': data.uid})


class NDMetricAnnotation:

    @classmethod
    def to_common(cls, annotation: NDDataRowScalarMetric) -> ScalarMetric:
        return annotation.to_common()

    @classmethod
    def from_common(cls, annotation: ScalarMetric,
                    data: Union[TextData, RasterData]) -> NDDataRowScalarMetric:
        return NDDataRowScalarMetric.from_common(annotation, data)


NDMetricType = NDDataRowScalarMetric
