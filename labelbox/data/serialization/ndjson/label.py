from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.annotation_types.geometry import line, point, rectangle
from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.classification.classification import Text, CheckList, Radio
from labelbox.data.annotation_types.annotation import AnnotationType, ClassificationAnnotation, ObjectAnnotation, VideoClassificationAnnotation
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.serialization.ndjson.objects import NDLine, NDMask, NDObject, NDObjectType, NDPoint, NDPolygon, NDRectangle, NDTextEntity
from labelbox.data.serialization.ndjson.classifications import NDCheckList, NDClassification, NDClassificationType, NDRadio, NDText
from typing import List, Union
from pydantic import BaseModel
from itertools import groupby
from operator import itemgetter


class NDLabel(BaseModel):
    annotations: List[Union[NDObjectType, NDClassificationType]]

    def to_common(self):
        # Should data have to already be in labelbox?
        # e.g. labels are going to have
        # Infer the data type based off the labels...
        # Group by data row id here... This is a flattened collection
        data_rows = {}
        for annotation in self.annotations:
            if annotation.dataRow.id in data_rows:
                data_rows[annotation.dataRow.id].append(annotation)
            else:
                data_rows[annotation.dataRow.id] = [annotation]

        def generate_annotations():
            for data_row_id, annotations in data_rows.items():
                annots = []
                for annotation in annotations:
                    if isinstance(annotation, NDObjectType.__args__):
                        annots.append(NDObject.to_common(annotation))
                    if isinstance(annotation, NDClassificationType.__args__):
                        annots.extend(NDClassification.to_common(annotation))
                    else:
                        raise TypeError(f"Unsupported annotation. {type(annotation.value)}")

                data = self.infer_media_types(annotations)(uid = data_row_id)
                yield Label(
                    annotations = annots,
                    data = data
                )
        return LabelCollection(data = generate_annotations())


    def infer_media_types(self, annotations):
        types = {type(annotation) for annotation in annotations}
        if TextEntity in types:
            return TextData
        elif VideoClassificationAnnotation in types:
            return VideoData
        else:
            return RasterData

    @classmethod
    def from_common(cls, data: LabelCollection):
        for label in data.data:
            video_annotations = {}
            for annot in label.annotations:
                if isinstance(annot, VideoClassificationAnnotation):
                    if annot.schema_id in video_annotations:
                        video_annotations[annot.schema_id].append(annot)
                    else:
                        video_annotations[annot.schema_id] = [annot]

            non_video_annotations = [annot for annot in label.annotations if not isinstance(annot, VideoClassificationAnnotation)]
            for annotation in non_video_annotations:
                if isinstance(annotation, ClassificationAnnotation):
                    yield NDClassification.from_common(annotation, label.data)
                elif isinstance(annotation, ObjectAnnotation):
                    yield NDObject.from_common(annotation, label.data)
                else:
                    raise TypeError(f"Unable to convert object to MAL format. `{type(annotation.value)}`")

            for annotation_group in video_annotations.values():
                consecutive_frames = cls.get_consecutive_frames(sorted([annotation.frame for annotation in annotation_group]))
                annotation = annotation_group[0]
                frames_data = []
                for frames in consecutive_frames:
                    frames_data.append({'start': frames[0], 'end': frames[-1]})
                annotation.extra.update({'frames' : frames_data})
                yield NDClassification.from_common(annotation, label.data)


    @staticmethod
    def get_consecutive_frames(data):
        consecutive = []
        for k, g in groupby(enumerate(data), lambda x:x[0]-x[1]):
            group = list(map(itemgetter(1), g))
            consecutive.append((group[0], group[-1]))
        return consecutive















