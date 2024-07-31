import copy
import logging
import uuid
from collections import defaultdict, deque
from typing import Any, Deque, Dict, Generator, Iterable, List, Set, Union

from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.data.annotation_types.classification.classification import (
    ClassificationAnnotation,)
from labelbox.data.annotation_types.metrics.confusion_matrix import (
    ConfusionMatrixMetric,)
from labelbox.data.annotation_types.metrics.scalar import ScalarMetric
from labelbox.data.annotation_types.video import VideoMaskAnnotation

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
        used_uuids: Set[uuid.UUID] = set()

        relationship_uuids: Dict[uuid.UUID,
                                 Deque[uuid.UUID]] = defaultdict(deque)

        # UUIDs are private properties used to enhance UX when defining relationships.
        # They are created for all annotations, but only utilized for relationships.
        # To avoid overwriting, UUIDs must be unique across labels.
        # Non-relationship annotation UUIDs are regenerated when they are reused.
        # For relationship annotations, during first pass, we update the UUIDs of the source and target annotations.
        # During the second pass, we update the UUIDs of the annotations referenced by the relationship annotations.
        for label in labels:
            uuid_safe_annotations: List[Union[
                ClassificationAnnotation,
                ObjectAnnotation,
                VideoMaskAnnotation,
                ScalarMetric,
                ConfusionMatrixMetric,
                RelationshipAnnotation,
            ]] = []
            # First pass to get all RelatiohnshipAnnotaitons
            # and update the UUIDs of the source and target annotations
            for annotation in label.annotations:
                if isinstance(annotation, RelationshipAnnotation):
                    annotation = copy.deepcopy(annotation)
                    new_source_uuid = uuid.uuid4()
                    new_target_uuid = uuid.uuid4()
                    relationship_uuids[annotation.value.source._uuid].append(
                        new_source_uuid)
                    relationship_uuids[annotation.value.target._uuid].append(
                        new_target_uuid)
                    annotation.value.source._uuid = new_source_uuid
                    annotation.value.target._uuid = new_target_uuid
                    if annotation._uuid in used_uuids:
                        annotation._uuid = uuid.uuid4()
                    used_uuids.add(annotation._uuid)
                    uuid_safe_annotations.append(annotation)
            # Second pass to update UUIDs for annotations referenced by RelationshipAnnotations
            for annotation in label.annotations:
                if (not isinstance(annotation, RelationshipAnnotation) and
                        hasattr(annotation, "_uuid")):
                    annotation = copy.deepcopy(annotation)
                    next_uuids = relationship_uuids[annotation._uuid]
                    if len(next_uuids) > 0:
                        annotation._uuid = next_uuids.popleft()

                    if annotation._uuid in used_uuids:
                        annotation._uuid = uuid.uuid4()
                    used_uuids.add(annotation._uuid)
                    uuid_safe_annotations.append(annotation)
                else:
                    if not isinstance(annotation, RelationshipAnnotation):
                        uuid_safe_annotations.append(annotation)
            label.annotations = uuid_safe_annotations
            for annotation in NDLabel.from_common([label]):
                annotation_uuid = getattr(annotation, "uuid", None)

                res = annotation.dict(
                    by_alias=True,
                    exclude={"uuid"} if annotation_uuid == "None" else None,
                )
                for k, v in list(res.items()):
                    if k in IGNORE_IF_NONE and v is None:
                        del res[k]
                if getattr(label, 'is_benchmark_reference'):
                    res['isBenchmarkReferenceLabel'] = True
                yield res
