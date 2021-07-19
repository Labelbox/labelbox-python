import logging
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue
from typing import Any, Callable, Dict, Generator, Iterable

import ndjson
import requests
from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.annotation_types.label import Label
from labelbox.data.serialization.labelbox_v1.label import LBV1Label

logger = logging.getLogger(__name__)


class LBV1Converter:
    @staticmethod
    def deserialize_video(json_data: Iterable[Dict[str, Any]], client):
        """
        This method is only necessary if the json payload for the data contains links to the video data.
        """
        label_generator = (LBV1Label(**example).to_common()
                           for example in VideoIterator(json_data, client))
        return LabelCollection(data=label_generator)

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelCollection:
        def label_generator():
            for example in json_data:
                if 'frames' in example['Label']:
                    raise ValueError("Use `LBV1Converter.deserialize_video` to process video")
                yield LBV1Label(**example).to_common()
        return LabelCollection(data=label_generator())

    @staticmethod
    def serialize(label_collection: LabelCollection,
                  signer: Callable) -> Generator[Dict[str, Any], None, None]:
        # Note that the signer is only used if the data object doesn't already have a url
        for label in label_collection.data:
            res = LBV1Label.from_common(label, signer)
            yield res.dict(by_alias=True)


class VideoIterator:
    def __init__(self, examples, client):
        self.queue = Queue(20)
        self.n_iters = len(examples)
        with ThreadPoolExecutor(max_workers=20) as executor:
            for example in examples:
                executor.submit(self.prefetch, example, client)

    def prefetch(self, example, client):
        try:
            if 'frames' in example['Label']:
                req = requests.get(
                    example['Label']['frames'],
                    headers={"Authorization": f"Bearer {client.api_key}"})
                example['Label'] = ndjson.loads(req.text)
            self.queue.put(example)
        except Exception as e:
            logger.warning(f"Unable to download frame. {e}")
            # If the frame is unable to be downloaded
            self.n_iters -= 1

    def __next__(self):
        if self.n_iters == 0:
            raise StopIteration("Iterated over all examples")
        self.n_iters -= 1
        res = self.queue.get()
        return res

    def __iter__(self):
        return self
