from typing import Any, Dict, Iterable, List
from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.serialization.labelbox_v1.label import LBV1Label


class LBV1Converter:

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelCollection:
        label_generator = (
            LBV1Label(**example).to_label() for example in json_data)
        return LabelCollection(data=label_generator)

    @staticmethod
    def serialize(label_collection: LabelCollection) -> List[Dict[str, Any]]:
        ...
        # TODO: construct objects from LabelCollection
        # Then call dict()
