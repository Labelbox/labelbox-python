import pytest
import labelbox.types as lb_types
from labelbox.data.annotation_types.audio import (
    AudioClassificationAnnotation,
    AudioObjectAnnotation,
)
from labelbox.data.annotation_types.classification.classification import (
    ClassificationAnswer,
    Radio,
    Text,
)
from labelbox.data.annotation_types.ner import TextEntity


def test_audio_classification_creation():
    """Test creating audio classification with direct frame specification"""
    annotation = AudioClassificationAnnotation(
        start_frame=2500,  # 2.5 seconds in milliseconds
        name="speaker_id",
        value=Radio(answer=ClassificationAnswer(name="john")),
    )

    assert annotation.start_frame == 2500
    assert annotation.end_frame is None
    assert annotation.segment_index is None
    assert annotation.name == "speaker_id"
    assert isinstance(annotation.value, Radio)
    assert annotation.value.answer.name == "john"


def test_audio_classification_with_time_range():
    """Test creating audio classification with start and end frames"""
    annotation = AudioClassificationAnnotation(
        start_frame=2500,  # Start at 2.5 seconds
        end_frame=4100,  # End at 4.1 seconds
        name="speaker_id",
        value=Radio(answer=ClassificationAnswer(name="john")),
    )

    assert annotation.start_frame == 2500
    assert annotation.end_frame == 4100
    assert annotation.name == "speaker_id"


def test_audio_classification_creation_with_segment():
    """Test creating audio classification with segment index"""
    annotation = AudioClassificationAnnotation(
        start_frame=10000,
        end_frame=15000,
        name="language",
        value=Radio(answer=ClassificationAnswer(name="english")),
        segment_index=1,
    )

    assert annotation.start_frame == 10000
    assert annotation.end_frame == 15000
    assert annotation.segment_index == 1


def test_audio_classification_text_type():
    """Test creating audio classification with Text value"""
    annotation = AudioClassificationAnnotation(
        start_frame=5000,  # 5.0 seconds
        name="quality",
        value=Text(answer="excellent"),
    )

    assert annotation.start_frame == 5000
    assert annotation.name == "quality"
    assert isinstance(annotation.value, Text)
    assert annotation.value.answer == "excellent"


def test_audio_object_creation():
    """Test creating audio object annotation"""
    annotation = AudioObjectAnnotation(
        start_frame=10000,
        end_frame=12500,
        name="transcription",
        value=lb_types.TextEntity(
            start=0, end=11
        ),  # "Hello world" has 11 characters
    )

    assert annotation.start_frame == 10000
    assert annotation.end_frame == 12500
    assert annotation.keyframe is True
    assert annotation.segment_index is None
    assert annotation.name == "transcription"
    assert isinstance(annotation.value, lb_types.TextEntity)
    assert annotation.value.start == 0
    assert annotation.value.end == 11


def test_audio_object_creation_with_classifications():
    """Test creating audio object with sub-classifications"""
    sub_classification = AudioClassificationAnnotation(
        start_frame=10000,
        name="confidence",
        value=Radio(answer=ClassificationAnswer(name="high")),
    )

    annotation = AudioObjectAnnotation(
        start_frame=10000,
        end_frame=12500,
        name="transcription",
        value=lb_types.TextEntity(start=0, end=11),
        classifications=[sub_classification],
    )

    assert len(annotation.classifications) == 1
    assert annotation.classifications[0].name == "confidence"
    assert annotation.classifications[0].start_frame == 10000


def test_audio_object_direct_creation():
    """Test creating audio object directly with various options"""
    annotation = AudioObjectAnnotation(
        start_frame=7500,  # 7.5 seconds
        name="sound_event",
        value=lb_types.TextEntity(start=0, end=11),
        keyframe=False,
        segment_index=2,
    )

    assert annotation.start_frame == 7500
    assert annotation.end_frame is None
    assert annotation.keyframe is False
    assert annotation.segment_index == 2


def test_frame_precision():
    """Test frame values maintain precision"""
    # Test various time values in milliseconds
    test_cases = [0, 1, 1000, 1500, 10123, 60000]

    for milliseconds in test_cases:
        annotation = AudioClassificationAnnotation(
            start_frame=milliseconds,
            end_frame=milliseconds + 1000,
            name="test",
            value=Text(answer="test"),
        )
        assert annotation.start_frame == milliseconds
        assert annotation.end_frame == milliseconds + 1000


def test_audio_label_integration():
    """Test audio annotations work with Label container"""
    # Create audio annotations
    speaker_annotation = AudioClassificationAnnotation(
        start_frame=1000,
        end_frame=2000,
        name="speaker",
        value=Radio(answer=ClassificationAnswer(name="john")),
    )

    transcription_annotation = AudioObjectAnnotation(
        start_frame=1000,
        end_frame=2000,
        name="transcription",
        value=lb_types.TextEntity(start=0, end=5),
    )

    # Create label with audio annotations
    label = lb_types.Label(
        data={"global_key": "audio_file.mp3"},
        annotations=[speaker_annotation, transcription_annotation],
    )

    # Verify annotations are accessible
    assert len(label.annotations) == 2

    # Check annotation types
    audio_classifications = [
        ann
        for ann in label.annotations
        if isinstance(ann, AudioClassificationAnnotation)
    ]
    audio_objects = [
        ann
        for ann in label.annotations
        if isinstance(ann, AudioObjectAnnotation)
    ]

    assert len(audio_classifications) == 1
    assert len(audio_objects) == 1
    assert audio_classifications[0].name == "speaker"
    assert audio_objects[0].name == "transcription"


def test_audio_annotation_validation():
    """Test audio annotation field validation"""
    # Test frame must be int
    with pytest.raises(ValueError):
        AudioClassificationAnnotation(
            start_frame="invalid",  # Should be int
            name="test",
            value=Text(answer="test"),
        )


def test_audio_annotation_extra_fields():
    """Test audio annotations can have extra metadata"""
    extra_data = {"source": "automatic", "confidence_score": 0.95}

    annotation = AudioClassificationAnnotation(
        start_frame=3000, name="quality", value=Text(answer="good"), extra=extra_data
    )

    assert annotation.extra["source"] == "automatic"
    assert annotation.extra["confidence_score"] == 0.95


def test_audio_annotation_feature_schema():
    """Test audio annotations with feature schema IDs"""
    annotation = AudioClassificationAnnotation(
        start_frame=4000,
        name="language",
        value=Radio(answer=ClassificationAnswer(name="spanish")),
        feature_schema_id="1234567890123456789012345",
    )

    assert annotation.feature_schema_id == "1234567890123456789012345"


def test_audio_annotation_mixed_types():
    """Test label with mixed audio and other annotation types"""
    # Audio annotation
    audio_annotation = AudioClassificationAnnotation(
        start_frame=2000,
        name="speaker",
        value=Radio(answer=ClassificationAnswer(name="john")),
    )

    # Video annotation
    video_annotation = lb_types.VideoClassificationAnnotation(
        start_frame=10, name="quality", value=Text(answer="good")
    )

    # Image annotation
    image_annotation = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=0, y=0), end=lb_types.Point(x=100, y=100)
        ),
    )

    # Create label with mixed types
    label = lb_types.Label(
        data={"global_key": "mixed_media"},
        annotations=[audio_annotation, video_annotation, image_annotation],
    )

    # Verify all annotations are present
    assert len(label.annotations) == 3

    # Check types
    audio_annotations = [
        ann
        for ann in label.annotations
        if isinstance(ann, AudioClassificationAnnotation)
    ]
    video_annotations = [
        ann
        for ann in label.annotations
        if isinstance(ann, lb_types.VideoClassificationAnnotation)
    ]
    object_annotations = [
        ann
        for ann in label.annotations
        if isinstance(ann, lb_types.ObjectAnnotation)
    ]

    assert len(audio_annotations) == 1
    assert len(video_annotations) == 1
    assert len(object_annotations) == 1


def test_audio_annotation_serialization():
    """Test audio annotations can be serialized to dict"""
    annotation = AudioClassificationAnnotation(
        start_frame=6000,
        end_frame=8000,
        name="emotion",
        value=Radio(answer=ClassificationAnswer(name="happy")),
        segment_index=3,
        extra={"confidence": 0.9},
    )

    # Test model_dump
    serialized = annotation.model_dump()
    assert serialized["frame"] == 6000
    assert serialized["end_frame"] == 8000
    assert serialized["name"] == "emotion"
    assert serialized["segment_index"] == 3
    assert serialized["extra"]["confidence"] == 0.9

    # Test model_dump with exclusions
    serialized_excluded = annotation.model_dump(exclude_none=True)
    assert "frame" in serialized_excluded
    assert "name" in serialized_excluded
    assert "end_frame" in serialized_excluded
    assert "segment_index" in serialized_excluded


def test_audio_annotation_from_dict():
    """Test audio annotations can be created from dict"""
    annotation_data = {
        "frame": 7000,
        "end_frame": 9000,
        "name": "topic",
        "value": Text(answer="technology"),
        "segment_index": 2,
        "extra": {"source": "manual"},
    }

    annotation = AudioClassificationAnnotation(**annotation_data)

    assert annotation.start_frame == 7000
    assert annotation.end_frame == 9000
    assert annotation.name == "topic"
    assert annotation.segment_index == 2
    assert annotation.extra["source"] == "manual"


def test_audio_annotation_edge_cases():
    """Test audio annotation edge cases"""
    # Test very long audio (many hours)
    long_annotation = AudioClassificationAnnotation(
        start_frame=3600000,  # 1 hour in milliseconds
        end_frame=7200000,  # 2 hours in milliseconds
        name="long_audio",
        value=Text(answer="very long"),
    )

    assert long_annotation.start_frame == 3600000
    assert long_annotation.end_frame == 7200000

    # Test very short audio (milliseconds)
    short_annotation = AudioClassificationAnnotation(
        start_frame=1,  # 1 millisecond
        end_frame=2,  # 2 milliseconds
        name="short_audio",
        value=Text(answer="very short"),
    )

    assert short_annotation.start_frame == 1
    assert short_annotation.end_frame == 2

    # Test zero time
    zero_annotation = AudioClassificationAnnotation(
        start_frame=0, name="zero_time", value=Text(answer="zero")
    )

    assert zero_annotation.start_frame == 0
    assert zero_annotation.end_frame is None


def test_temporal_annotation_grouping():
    """Test that annotations with same name can be grouped for temporal processing"""
    # Create multiple annotations with same name (like tokens)
    tokens = ["Hello", "world", "this", "is", "audio"]
    annotations = []

    for i, token in enumerate(tokens):
        start_frame = i * 1000  # 1 second apart
        end_frame = start_frame + 900  # 900ms duration each

        annotation = AudioClassificationAnnotation(
            start_frame=start_frame,
            end_frame=end_frame,
            name="tokens",  # Same name for grouping
            value=Text(answer=token),
        )
        annotations.append(annotation)

    # Verify all have same name but different content and timing
    assert len(annotations) == 5
    assert all(ann.name == "tokens" for ann in annotations)
    assert annotations[0].value.answer == "Hello"
    assert annotations[1].value.answer == "world"
    assert annotations[0].start_frame == 0
    assert annotations[1].start_frame == 1000
    assert annotations[0].end_frame == 900
    assert annotations[1].end_frame == 1900


def test_audio_object_types():
    """Test different types of audio object annotations"""
    # Text entity (transcription)
    text_obj = AudioObjectAnnotation(
        start_frame=1000,
        name="transcription",
        value=TextEntity(start=0, end=5),  # "hello"
    )

    assert isinstance(text_obj.value, TextEntity)
    assert text_obj.value.start == 0
    assert text_obj.value.end == 5

    # Test with keyframe and segment settings
    keyframe_obj = AudioObjectAnnotation(
        start_frame=2000,
        end_frame=3000,
        name="segment",
        value=TextEntity(start=10, end=15),
        keyframe=True,
        segment_index=1,
    )

    assert keyframe_obj.keyframe is True
    assert keyframe_obj.segment_index == 1
    assert keyframe_obj.start_frame == 2000
    assert keyframe_obj.end_frame == 3000
