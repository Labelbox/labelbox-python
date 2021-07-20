import logging
from typing import Any, Dict, Generator, Iterable

from ...annotation_types.collection import LabelData, LabelGenerator
from .label import NDLabel

logger = logging.getLogger(__name__)


class NDJsonConverter:

    @staticmethod
    def deserialize(json_data: Iterable[Dict[str, Any]]) -> LabelGenerator:
        """
        Converts ndjson data (prediction import format) into the common labelbox format.

        Args:
            json_data: An iterable representing the ndjson data
        Returns:
            LabelGenerator containing the ndjson data.
        """
        data = NDLabel(**{'annotations': json_data})
        return data.to_common()

    @staticmethod
    def serialize(labels: LabelData) -> Generator[Dict[str, Any], None, None]:
        """
        Converts a labelbox common object to the labelbox ndjson format (prediction import format)

        Args:
            labels: Either a LabelCollection or a LabelGenerator
        Returns:
            A generator for accessing the ndjson representation of the data
        """
        for example in NDLabel.from_common(labels):
            yield example.dict(by_alias=True)
