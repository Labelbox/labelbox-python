import logging
from typing import Any, Dict, Generator


from ...annotation_types.collection import LabelCollection
from .label import NDLabel

logger = logging.getLogger(__name__)

IGNORE_IF_NONE = ["page", "unit", "messageId"]


class NDJsonConverter:
    @staticmethod
    def serialize(
        labels: LabelCollection,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Converts a labelbox common object to the labelbox ndjson format (prediction import format)

        Note that this function might fail for objects that are not supported by mal.
        Not all edge cases are handling by custom exceptions, if you get a cryptic pydantic error message it is probably due to this.
        We will continue to improve the error messages and add helper functions to deal with this.

        Args:
            labels: Either a list of Label objects or a LabelGenerator
        Returns:
            A generator for accessing the ndjson representation of the data
        """

        for label in labels:
            for example in NDLabel.from_common([label]):
                annotation_uuid = getattr(example, "uuid", None)
                res = example.model_dump(
                    exclude_none=True,
                    by_alias=True,
                    exclude={"uuid"} if annotation_uuid == "None" else None,
                )
                for k, v in list(res.items()):
                    if k in IGNORE_IF_NONE and v is None:
                        del res[k]
                if getattr(label, "is_benchmark_reference"):
                    res["isBenchmarkReferenceLabel"] = True
                yield res
