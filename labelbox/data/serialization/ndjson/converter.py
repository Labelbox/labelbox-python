import logging
from typing import Any, Dict, Generator, Iterable

from labelbox.data.annotation_types.collection import LabelCollection

from .label import NDLabel

logger = logging.getLogger(__name__)

# TODO: Support videos


class NDJsonConverter:

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelCollection:
        data = NDLabel(**{'annotations': json_data})
        return data.to_common()

    @staticmethod
    def serialize(
        label_collection: LabelCollection
    ) -> Generator[Dict[str, Any], None, None]:

        for example in NDLabel.from_common(label_collection):
            yield example.dict(by_alias=True)
