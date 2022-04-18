from itertools import groupby
from operator import itemgetter
from typing import Dict, Generator, List, Tuple, Union
from collections import defaultdict
import warnings

from pydantic import BaseModel

from ...annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation, VideoClassificationAnnotation, VideoObjectAnnotation
from ...annotation_types.collection import LabelCollection, LabelGenerator
from ...annotation_types.data import ImageData, TextData, VideoData
from ...annotation_types.label import Label
from ...annotation_types.ner import TextEntity
from ...annotation_types.classification import Dropdown
from ...annotation_types.metrics import ScalarMetric, ConfusionMatrixMetric

from .metric import NDScalarMetric, NDMetricAnnotation, NDConfusionMatrixMetric
from .classification import NDChecklistSubclass, NDClassification, NDClassificationType, NDRadioSubclass
from .objects import NDObject, NDObjectType, NDSegments


class NDLabel(BaseModel):
    annotations: List[Union[NDObjectType, NDClassificationType,
                            NDConfusionMatrixMetric, NDScalarMetric,
                            NDSegments]]

    def to_common(self) -> LabelGenerator:
        grouped_annotations = defaultdict(list)
        for annotation in self.annotations:
            grouped_annotations[annotation.data_row.id].append(annotation)
        return LabelGenerator(
            data=self._generate_annotations(grouped_annotations))

    @classmethod
    def from_common(cls,
                    data: LabelCollection) -> Generator["NDLabel", None, None]:
        for label in data:
            yield from cls._create_non_video_annotations(label)
            yield from cls._create_video_annotations(label)

    def _generate_annotations(
        self,
        grouped_annotations: Dict[str,
                                  List[Union[NDObjectType, NDClassificationType,
                                             NDConfusionMatrixMetric,
                                             NDScalarMetric, NDSegments]]]
    ) -> Generator[Label, None, None]:
        for data_row_id, annotations in grouped_annotations.items():
            annots = []
            for annotation in annotations:
                if isinstance(annotation, NDSegments):
                    annots.extend(
                        NDSegments.to_common(annotation, annotation.schema_id))

                elif isinstance(annotation, NDObjectType.__args__):
                    annots.append(NDObject.to_common(annotation))
                elif isinstance(annotation, NDClassificationType.__args__):
                    annots.extend(NDClassification.to_common(annotation))
                elif isinstance(annotation,
                                (NDScalarMetric, NDConfusionMatrixMetric)):
                    annots.append(NDMetricAnnotation.to_common(annotation))
                else:
                    raise TypeError(
                        f"Unsupported annotation. {type(annotation)}")
            data = self._infer_media_type(annotations)(uid=data_row_id)
            yield Label(annotations=annots, data=data)

    def _infer_media_type(
        self, annotations: List[Union[NDObjectType, NDClassificationType]]
    ) -> Union[TextEntity, TextData, ImageData]:
        types = {type(annotation) for annotation in annotations}
        if TextEntity in types:
            return TextData
        elif VideoClassificationAnnotation in types or VideoObjectAnnotation in types:
            return VideoData
        else:
            return ImageData

    @staticmethod
    def _get_consecutive_frames(
            frames_indices: List[int]) -> List[Tuple[int, int]]:
        consecutive = []
        for k, g in groupby(enumerate(frames_indices), lambda x: x[0] - x[1]):
            group = list(map(itemgetter(1), g))
            consecutive.append((group[0], group[-1]))
        return consecutive

    @classmethod
    def _create_video_annotations(
        cls, label: Label
    ) -> Generator[Union[NDChecklistSubclass, NDRadioSubclass], None, None]:

        video_annotations = defaultdict(list)
        for annot in label.annotations:
            if isinstance(
                    annot,
                (VideoClassificationAnnotation, VideoObjectAnnotation)):
                video_annotations[annot.feature_schema_id].append(annot)

        for annotation_group in video_annotations.values():
            consecutive_frames = cls._get_consecutive_frames(
                sorted([annotation.frame for annotation in annotation_group]))

            if isinstance(annotation_group[0], VideoClassificationAnnotation):
                annotation = annotation_group[0]
                frames_data = []
                for frames in consecutive_frames:
                    frames_data.append({'start': frames[0], 'end': frames[-1]})
                annotation.extra.update({'frames': frames_data})
                yield NDClassification.from_common(annotation, label.data)

            elif isinstance(annotation_group[0], VideoObjectAnnotation):
                warnings.warn(
                    """Nested classifications are not currently supported
                    for video object annotations
                    and will not import alongside the object annotations.""")
                segments = []
                for start_frame, end_frame in consecutive_frames:
                    segment = []
                    for annotation in annotation_group:
                        if annotation.keyframe and start_frame <= annotation.frame <= end_frame:
                            segment.append(annotation)
                    segments.append(segment)
                yield NDObject.from_common(segments, label.data)

    @classmethod
    def _create_non_video_annotations(cls, label: Label):
        non_video_annotations = [
            annot for annot in label.annotations
            if not isinstance(annot, (VideoClassificationAnnotation,
                                      VideoObjectAnnotation))
        ]
        for annotation in non_video_annotations:
            if isinstance(annotation, ClassificationAnnotation):
                if isinstance(annotation.value, Dropdown):
                    raise ValueError(
                        "Dropdowns are not supported by the NDJson format."
                        " Please filter out Dropdown annotations before converting."
                    )
                yield NDClassification.from_common(annotation, label.data)
            elif isinstance(annotation, ObjectAnnotation):
                yield NDObject.from_common(annotation, label.data)
            elif isinstance(annotation, (ScalarMetric, ConfusionMatrixMetric)):
                yield NDMetricAnnotation.from_common(annotation, label.data)
            else:
                raise TypeError(
                    f"Unable to convert object to MAL format. `{type(getattr(annotation, 'value',annotation))}`"
                )
