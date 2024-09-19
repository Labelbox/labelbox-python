from typing import Any, Dict, List, Optional

from lbox.classification.classification_annotation import ClassificationAnnotation
from pydantic import BaseModel, model_serializer

from .data_row import DataRow


class Label(BaseModel):
    """Container for holding data and annotations

    >>> Label(
    >>>    data = {'global_key': 'my-data-row-key'} # also accepts uid
    >>>    annotations = [
    >>>        ObjectAnnotation(
    >>>            value = Point(x = 10, y = 10),
    >>>            name = "target"
    >>>        )
    >>>     ]
    >>>  )

    Args:
        uid: Optional Label Id in Labelbox
        data: Data of Label, Image, Video, Text or dict with a single key uid | global_key | external_id.
            Note use of classes as data is deprecated. Use GenericDataRowData or dict with a single key instead.
        annotations: List of Annotations in the label
        extra: additional context
    """

    uid: Optional[str] = None
    data_row: DataRow
    annotations: List[ClassificationAnnotation] = []
    extra: Dict[str, Any] = {}
    is_benchmark_reference: Optional[bool] = False

    @model_serializer(mode='wrap')
    def serialize_label(self, handler, info):
        res = handler(self)
        if res["is_benchmark_reference"] is False:
            res.pop("is_benchmark_reference")

        for annotation in res["annotations"]:
            annotation["data_row"] = res["data_row"]
        return res
