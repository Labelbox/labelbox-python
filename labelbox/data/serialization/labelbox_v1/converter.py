from typing import Any, Callable, Dict, Generator, Iterable
import logging

import ndjson
import requests

from ...annotation_types.collection import (LabelData, LabelGenerator,
                                            PrefetchGenerator)
from .label import LBV1Label

logger = logging.getLogger(__name__)


class LBV1Converter:

    @staticmethod
    def deserialize_video(json_data: Iterable[Dict[str, Any]], client):
        """
        This method is only necessary if the json payload for the data contains links to the video data.
        """
        label_generator = (LBV1Label(**example).to_common()
                           for example in LBV1VideoIterator(json_data, client))
        return LabelGenerator(data=label_generator)

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelGenerator:

        def label_generator():
            for example in json_data:
                if 'frames' in example['Label']:
                    raise ValueError(
                        "Use `LBV1Converter.deserialize_video` to process video"
                    )
                yield LBV1Label(**example).to_common()

        return LabelGenerator(data=label_generator())

    @staticmethod
    def serialize(labels: LabelData,
                  signer: Callable) -> Generator[Dict[str, Any], None, None]:
        # Note that the signer is only used if the data object doesn't already have a url
        for label in labels:
            res = LBV1Label.from_common(label, signer)
            yield res.dict(by_alias=True)


class LBV1VideoIterator(PrefetchGenerator):

    def __init__(self, examples, client):
        self.client = client

        super().__init__(examples)

    def process(self, value):
        if 'frames' in value['Label']:
            req = requests.get(
                value['Label']['frames'],
                headers={"Authorization": f"Bearer {self.client.api_key}"})
            value['Label'] = ndjson.loads(req.text)
            return value
