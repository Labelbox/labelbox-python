from typing import Any, Callable, Dict, Iterable, List, Generator
from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.serialization.labelbox_v1.label import LBV1Label


class LBV1Converter:

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelCollection:
        label_generator = (
            LBV1Label(**example).to_common() for example in json_data)

        return LabelCollection(data=label_generator)

    @staticmethod
    def serialize(label_collection: LabelCollection,
                  signer: Callable) -> Generator[Dict[str, Any], None, None]:
        # Note that the signer is only used if the data object doesn't already have a url

        for label in label_collection.data:
            # By alias so we can support keys with spaces in them..
            res = LBV1Label.from_common(label, signer).dict(by_alias=True)
            yield res





