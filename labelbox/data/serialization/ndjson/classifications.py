from labelbox.data.annotation_types.annotation import AnnotationType, ClassificationAnnotation, VideoClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import ClassificationAnswer, Dropdown, Text, CheckList, Radio
from typing import List, Union, Optional
from labelbox.data.serialization.ndjson.base import NDAnnotation
from pydantic import BaseModel, Field


class NDFeature(BaseModel):
    schemaId : str #= Field(..., alias = 'schemaId')
    # TODO: Nice warning message telling users to assign a schema_id if none


class FrameLocation(BaseModel):
    end: int
    start: int


class VideoSupported(BaseModel):
    #Note that frames are only allowed as top level inferences for video
    frames: Optional[List[FrameLocation]] = None

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        # This means these are no video frames ..
        if self.frames is None:
            res.pop('frames')
        return res


class NDTextSubclass(NDFeature):
    answer: str

    def to_common(self):
        return Text(
            answer = self.answer
        )

    @classmethod
    def from_common(cls, annotation):
        return cls(
            answer = annotation.value.answer,
            schemaId = annotation.schema_id
        )


class NDCheckListSubclass(NDFeature):
    answer: List[NDFeature]

    def to_common(self):
        return CheckList(
            answer = [ClassificationAnswer(schema_id = answer.schemaId) for answer in  self.answer]
        )


    @classmethod
    def from_common(cls, annotation):
        return cls(
            answer = [NDFeature(schemaId = answer.schema_id) for answer in annotation.value.answer],
            schemaId = annotation.schema_id
        )

class NDRadioSubclass(NDFeature):
    answer: NDFeature

    def to_common(self):
        return Radio(
            answer = ClassificationAnswer(schema_id = self.answer.schemaId)
        )

    @classmethod
    def from_common(cls, annotation):
        return cls(
            answer = NDFeature(schemaId = annotation.value.answer.schema_id),
            schemaId = annotation.schema_id
        )


class NDText(NDAnnotation, NDTextSubclass):

    @classmethod
    def from_common(cls, annotation, data):
        return cls(
            answer = annotation.value.answer,
            dataRow = {'id' : data.uid},
            schemaId = annotation.schema_id,
            uuid = annotation.extra.get('uuid'),
        )


class NDCheckList(NDAnnotation, NDCheckListSubclass, VideoSupported):
    ...

    @classmethod
    def from_common(cls, annotation, data):
        return cls(
            answer = [NDFeature(schemaId = answer.schema_id) for answer in annotation.value.answer],
            dataRow = {'id' : data.uid},
            schemaId = annotation.schema_id,
            uuid = annotation.extra.get('uuid'),
            frames = annotation.extra.get('frames')
        )

class NDRadio(NDAnnotation, NDRadioSubclass, VideoSupported):

    @classmethod
    def from_common(cls, annotation, data):
        return cls(
            answer = NDFeature(schemaId = annotation.value.answer.schema_id),
            dataRow = {'id' : data.uid},
            schemaId = annotation.schema_id,
            uuid = annotation.extra.get('uuid'),
            frames = annotation.extra.get('frames')
        )

class NDSubclassification:
    @classmethod
    def from_common(cls, annotation: AnnotationType):
        classify_obj = cls.lookup_subclassification(annotation)
        if classify_obj is None:
            raise TypeError(f"Unable to convert object to MAL format. `{type(annotation.value)}`")
        return classify_obj.from_common(annotation)

    @staticmethod
    def to_common(annotation: AnnotationType):
        return ClassificationAnnotation(value =  annotation.to_common(), schema_id = annotation.schemaId)

    @staticmethod
    def lookup_subclassification(annotation: AnnotationType):
        if isinstance(annotation, Dropdown):
            raise TypeError("Dropdowns are not supported for MAL")
        return {
            Text: NDTextSubclass,
            CheckList: NDCheckListSubclass,
            Radio: NDRadioSubclass,
        }.get(type(annotation.value))

class NDClassification:
    @classmethod
    def from_common(cls, annotation: AnnotationType, data):
        classify_obj = cls.lookup_classification(annotation)
        if classify_obj is None:
            raise TypeError(f"Unable to convert object to MAL format. `{type(annotation.value)}`")
        return classify_obj.from_common(annotation, data)

    @staticmethod
    def to_common(annotation: AnnotationType):
        common = ClassificationAnnotation(value =  annotation.to_common(), schema_id = annotation.schemaId, extra = {'uuid' : annotation.uuid})
        if getattr(annotation, 'frames', None) is None:
            return [common]
        results = []
        for frame in annotation.frames:
            for idx in range(frame.start, frame.end + 1, 1):
                results.append(VideoClassificationAnnotation(frame = idx,**common.dict()))
        return results

    @staticmethod
    def lookup_classification(annotation: AnnotationType):
        if isinstance(annotation, Dropdown):
            raise TypeError("Dropdowns are not supported for MAL")
        return {
            Text: NDText,
            CheckList: NDCheckList,
            Radio: NDRadio,
            Dropdown: NDCheckList,
        }.get(type(annotation.value))



NDSubclassificationType = Union[NDRadioSubclass, NDCheckListSubclass, NDTextSubclass]
NDClassificationType = Union[NDRadio, NDCheckList, NDText]
