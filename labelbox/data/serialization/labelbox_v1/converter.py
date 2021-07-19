from typing import Any, Callable, Dict, Iterable, List, Generator
import logging
from multiprocessing import Queue
from concurrent.futures import ThreadPoolExecutor

import requests
import ndjson

from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.serialization.labelbox_v1.label import LBV1Label
from labelbox.data.annotation_types.label import Label

logger = logging.getLogger(__name__)


class LBV1Converter:

    @staticmethod
    def deserialize_video(json_data: Iterable[Dict[str, Any]], client):
        # Use a queue to limit the number of cached example - only fetch as needed..
        label_generator = (LBV1Label(**example).to_common(is_video=True)
                           for example in VideoIterator(json_data, client))
        return LabelCollection(data=label_generator)

    #TODO: Deserialize should work with the serialized payload.
    # So json data can also be an updated video
    # Instead of is_video being an option. We should just see if the frame data is a list. Also look for .mp4 or something.

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
            res = LBV1Label.from_common(label, signer)
            yield res.dict(by_alias=True)


class VideoIterator:

    def __init__(self, examples, client):
        print
        self.queue = Queue(20)
        self.futures = []
        self.n_iters = len(examples)
        with ThreadPoolExecutor(max_workers=20) as executor:
            for example in examples:
                self.futures.append(
                    executor.submit(self.prefetch, example, client))

    def prefetch(self, example, client):
        try:
            if 'frames' in example['Label']:
                req = requests.get(
                    example['Label']['frames'],
                    headers={"Authorization": f"Bearer {client.api_key}"})
                #example['Label'] = [ndjson.loads(req.text)[0]] # TODO: Remove this. This is just for testing...
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
