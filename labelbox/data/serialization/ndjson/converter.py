import logging
from typing import Any, Dict, Generator, Iterable

from ...annotation_types.collection import LabelData, LabelGenerator
from .label import NDLabel

logger = logging.getLogger(__name__)


class NDJsonConverter:

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelGenerator:
        data = NDLabel(**{'annotations': json_data})
        return data.to_common()

    @staticmethod
    def serialize(labels: LabelData) -> Generator[Dict[str, Any], None, None]:

        for example in NDLabel.from_common(labels):
            yield example.dict(by_alias=True)
