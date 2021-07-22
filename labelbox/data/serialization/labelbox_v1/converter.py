from requests.exceptions import HTTPError
import labelbox
from typing import Any, Dict, Generator, Iterable
import logging

import ndjson
import requests
from google.api_core import retry

from .label import LBV1Label
from ...annotation_types.collection import (LabelContainer, LabelGenerator,
                                            PrefetchGenerator)

logger = logging.getLogger(__name__)


class LBV1Converter:

    @staticmethod
    def deserialize_video(json_data: Iterable[Dict[str, Any]], client):
        """
        Converts a labelbox video export into the common labelbox format.

        Args:
            json_data: An iterable representing the labelbox video export.
        Returns:
            LabelGenerator containing the video data.
        """
        label_generator = (LBV1Label(**example).to_common()
                           for example in LBV1VideoIterator(json_data, client))
        return LabelGenerator(data=label_generator)

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelGenerator:
        """
        Converts a labelbox export (non-video) into the common labelbox format.

        Args:
            json_data: An iterable representing the labelbox export.
        Returns:
            LabelGenerator containing the export data.
        """

        def label_generator():
            for example in json_data:
                if 'frames' in example['Label']:
                    raise ValueError(
                        "Use `LBV1Converter.deserialize_video` to process video"
                    )
                yield LBV1Label(**example).to_common()

        return LabelGenerator(data=label_generator())

    @staticmethod
    def serialize(
            labels: LabelContainer) -> Generator[Dict[str, Any], None, None]:
        """
        Converts a labelbox common object to the labelbox json export format

        Args:
            labels: Either a LabelCollection or a LabelGenerator
        Returns:
            A generator for accessing the labelbox json export representation of the data
        """
        for label in labels:
            res = LBV1Label.from_common(label)
            yield res.dict(by_alias=True)


class LBV1VideoIterator(PrefetchGenerator):
    """
    Generator that fetches video annotations in the background to be faster.
    """

    def __init__(self, examples, client):
        self.client = client
        super().__init__(examples)

    def _process(self, value):
        if 'frames' in value['Label']:
            req = self._request(value)
            value['Label'] = ndjson.loads(req)
            return value

    @retry.Retry(predicate=retry.if_exception_type(HTTPError))
    def _request(self, value):
        req = requests.get(
            value['Label']['frames'],
            headers={"Authorization": f"Bearer {self.client.api_key}"})
        if req.status_code == 401:
            raise labelbox.exceptions.AuthenticationError("Invalid API key")
        req.raise_for_status()
        return req.text
