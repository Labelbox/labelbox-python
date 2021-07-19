import logging
from multiprocessing import Queue
from typing import Any, Callable, Dict, Generator, Iterable
from .label import NDLabel

from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.annotation_types.label import Label
from labelbox.data.serialization.labelbox_v1.label import LBV1Label

logger = logging.getLogger(__name__)

# TODO: Support videos

class NDJsonConverter:
    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelCollection:
        data = NDLabel(**{'annotations' : json_data})
        return data.to_common()

    @staticmethod
    def serialize(label_collection: LabelCollection) -> Generator[Dict[str, Any], None, None]:
        # Note that the signer is only used if the data object doesn't already have a url
        # TODO: It is super important that this works with all data types.
        # We want users to be able to upload easily from these objects
        for example in NDLabel.from_common(label_collection):
            yield example.dict(by_alias = True)



