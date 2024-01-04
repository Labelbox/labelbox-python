import logging
import uuid
from typing import Any, Dict, Generator, Iterable

from ...annotation_types.collection import LabelCollection, LabelGenerator
from ...annotation_types.relationship import RelationshipAnnotation
from .label import NDLabel

logger = logging.getLogger(__name__)

IGNORE_IF_NONE = ["page", "unit", "messageId"]


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
        data = NDLabel(**{"annotations": json_data})
        res = data.to_common()
        return res

    @staticmethod
    def serialize(
            labels: LabelCollection) -> Generator[Dict[str, Any], None, None]:
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
        used_annotation_uuids = set()
        for label in labels:
            annotation_uuid_to_generated_uuid_lookup = {}
            # UUIDs are private properties used to enhance UX when defining relationships.
            # They are created for all annotations, but only utilized for relationships.
            # To avoid overwriting, UUIDs must be unique across labels.
            # Non-relationship annotation UUIDs are dropped (server-side generation will occur).
            # For relationship annotations, new UUIDs are generated and stored in a lookup table.
            for annotation in label.annotations:
                if isinstance(annotation, RelationshipAnnotation):
                    source_uuid = annotation.value.source._uuid
                    target_uuid = annotation.value.target._uuid

                    if (len(
                            used_annotation_uuids.intersection(
                                {source_uuid, target_uuid})) > 0):
                        new_source_uuid = uuid.uuid4()
                        new_target_uuid = uuid.uuid4()

                        annotation_uuid_to_generated_uuid_lookup[
                            source_uuid] = new_source_uuid
                        annotation_uuid_to_generated_uuid_lookup[
                            target_uuid] = new_target_uuid
                        annotation.value.source._uuid = new_source_uuid
                        annotation.value.target._uuid = new_target_uuid
                    else:
                        annotation_uuid_to_generated_uuid_lookup[
                            source_uuid] = source_uuid
                        annotation_uuid_to_generated_uuid_lookup[
                            target_uuid] = target_uuid
                    used_annotation_uuids.add(annotation._uuid)

            for annotation in label.annotations:
                if (not isinstance(annotation, RelationshipAnnotation) and
                        hasattr(annotation, "_uuid")):
                    annotation._uuid = annotation_uuid_to_generated_uuid_lookup.get(
                        annotation._uuid, annotation._uuid)

        for example in NDLabel.from_common(labels):
            annotation_uuid = getattr(example, "uuid", None)

            res = example.dict(
                by_alias=True,
                exclude={"uuid"} if annotation_uuid == "None" else None)
            for k, v in list(res.items()):
                if k in IGNORE_IF_NONE and v is None:
                    del res[k]
            yield res
