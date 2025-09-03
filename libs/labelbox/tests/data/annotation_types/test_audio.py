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
    Checklist,
)
from labelbox.data.annotation_types.ner import TextEntity


def test_audio_classification_creation():
    """Test creating audio classification with time range"""
    annotation = AudioClassificationAnnotation.from_time_range(
        start_sec=2.5,
        end_sec=4.1,
        name="speaker_id",
        value=Radio(answer=ClassificationAnswer(name="john"))
    )
    
    assert annotation.frame == 2500  # 2.5 seconds * 1000
    assert annotation.start_time == 2.5
    assert annotation.segment_index is None
    assert annotation.name == "speaker_id"
    assert isinstance(annotation.value, Radio)
    assert annotation.value.answer.name == "john"


def test_audio_classification_creation_with_segment():
    """Test creating audio classification with segment index"""
    annotation = AudioClassificationAnnotation.from_time_range(
        start_sec=10.0,
        end_sec=15.0,
        name="language",
        value=Radio(answer=ClassificationAnswer(name="english")),
        segment_index=1
    )
    
    assert annotation.frame == 10000
    assert annotation.start_time == 10.0
    assert annotation.segment_index == 1


def test_audio_classification_direct_creation():
    """Test creating audio classification directly with frame"""
    annotation = AudioClassificationAnnotation(
        frame=5000,  # 5.0 seconds
        name="quality",
        value=Text(answer="excellent")
    )
    
    assert annotation.frame == 5000
    assert annotation.start_time == 5.0
    assert annotation.name == "quality"
    assert isinstance(annotation.value, Text)
    assert annotation.value.answer == "excellent"


def test_audio_object_creation():
    """Test creating audio object annotation"""
    annotation = AudioObjectAnnotation.from_time_range(
        start_sec=10.0,
        end_sec=12.5,
        name="transcription",
        value=lb_types.TextEntity(start=0, end=11)  # "Hello world" has 11 characters
    )
    
    assert annotation.frame == 10000
    assert annotation.start_time == 10.0
    assert annotation.keyframe is True
    assert annotation.segment_index is None
    assert annotation.name == "transcription"
    assert isinstance(annotation.value, lb_types.TextEntity)
    assert annotation.value.start == 0
    assert annotation.value.end == 11


def test_audio_object_creation_with_classifications():
    """Test creating audio object with sub-classifications"""
    sub_classification = AudioClassificationAnnotation(
        frame=10000,
        name="confidence",
        value=Radio(answer=ClassificationAnswer(name="high"))
    )
    
    annotation = AudioObjectAnnotation.from_time_range(
        start_sec=10.0,
        end_sec=12.5,
        name="transcription",
        value=lb_types.TextEntity(start=0, end=11),  # "Hello world" has 11 characters
        classifications=[sub_classification]
    )
    
    assert len(annotation.classifications) == 1
    assert annotation.classifications[0].name == "confidence"
    assert annotation.classifications[0].frame == 10000


def test_audio_object_direct_creation():
    """Test creating audio object directly with frame"""
    annotation = AudioObjectAnnotation(
        frame=7500,  # 7.5 seconds
        name="sound_event",
        value=lb_types.TextEntity(start=0, end=11),  # "Dog barking" has 11 characters
        keyframe=False,
        segment_index=2
    )
    
    assert annotation.frame == 7500
    assert annotation.start_time == 7.5
    assert annotation.keyframe is False
    assert annotation.segment_index == 2


def test_time_conversion_precision():
    """Test time conversion maintains precision"""
    # Test various time values
    test_cases = [
        (0.0, 0),
        (0.001, 1),      # 1 millisecond
        (1.0, 1000),     # 1 second
        (1.5, 1500),     # 1.5 seconds
        (10.123, 10123), # 10.123 seconds
        (60.0, 60000),   # 1 minute
    ]
    
    for seconds, expected_milliseconds in test_cases:
        annotation = AudioClassificationAnnotation.from_time_range(
            start_sec=seconds,
            end_sec=seconds + 1.0,
            name="test",
            value=Text(answer="test")
        )
        assert annotation.frame == expected_milliseconds
        assert annotation.start_time == seconds


def test_audio_label_integration():
    """Test audio annotations in Label container"""
    # Create audio annotations
    speaker_annotation = AudioClassificationAnnotation.from_time_range(
        start_sec=1.0, end_sec=2.0,
        name="speaker", value=Radio(answer=ClassificationAnswer(name="john"))
    )
    
    transcription_annotation = AudioObjectAnnotation.from_time_range(
        start_sec=1.0, end_sec=2.0,
        name="transcription", value=lb_types.TextEntity(start=0, end=5)  # "Hello" has 5 characters
    )
    
    # Create label with audio annotations
    label = lb_types.Label(
        data={"global_key": "audio_file.mp3"},
        annotations=[speaker_annotation, transcription_annotation]
    )
    
    # Test audio annotations by frame
    audio_frames = label.audio_annotations_by_frame()
    assert 1000 in audio_frames
    assert len(audio_frames[1000]) == 2
    
    # Verify both annotations are in the same frame
    frame_annotations = audio_frames[1000]
    assert any(isinstance(ann, AudioClassificationAnnotation) for ann in frame_annotations)
    assert any(isinstance(ann, AudioObjectAnnotation) for ann in frame_annotations)


def test_audio_annotations_by_frame_empty():
    """Test audio_annotations_by_frame with no audio annotations"""
    label = lb_types.Label(
        data={"global_key": "image_file.jpg"},
        annotations=[
            lb_types.ObjectAnnotation(
                name="bbox",
                value=lb_types.Rectangle(
                    start=lb_types.Point(x=0, y=0),
                    end=lb_types.Point(x=100, y=100)
                )
            )
        ]
    )
    
    audio_frames = label.audio_annotations_by_frame()
    assert audio_frames == {}


def test_audio_annotations_by_frame_multiple_frames():
    """Test audio_annotations_by_frame with multiple time frames"""
    # Create annotations at different times
    annotation1 = AudioClassificationAnnotation(
        frame=1000,  # 1.0 seconds
        name="speaker1",
        value=Radio(answer=ClassificationAnswer(name="john"))
    )
    
    annotation2 = AudioClassificationAnnotation(
        frame=5000,  # 5.0 seconds
        name="speaker2",
        value=Radio(answer=ClassificationAnswer(name="jane"))
    )
    
    annotation3 = AudioObjectAnnotation(
        frame=1000,  # 1.0 seconds (same as annotation1)
        name="transcription1",
        value=lb_types.TextEntity(start=0, end=5)  # "Hello" has 5 characters
    )
    
    label = lb_types.Label(
        data={"global_key": "audio_file.mp3"},
        annotations=[annotation1, annotation2, annotation3]
    )
    
    audio_frames = label.audio_annotations_by_frame()
    
    # Should have 2 frames: 1000ms and 5000ms
    assert len(audio_frames) == 2
    assert 1000 in audio_frames
    assert 5000 in audio_frames
    
    # Frame 1000 should have 2 annotations
    assert len(audio_frames[1000]) == 2
    assert any(ann.name == "speaker1" for ann in audio_frames[1000])
    assert any(ann.name == "transcription1" for ann in audio_frames[1000])
    
    # Frame 5000 should have 1 annotation
    assert len(audio_frames[5000]) == 1
    assert audio_frames[5000][0].name == "speaker2"


def test_audio_annotation_validation():
    """Test audio annotation field validation"""
    # Test frame must be int
    with pytest.raises(ValueError):
        AudioClassificationAnnotation(
            frame="invalid",  # Should be int
            name="test",
            value=Text(answer="test")
        )
    
    # Test frame must be non-negative (Pydantic handles this automatically)
    # Negative frames are allowed by Pydantic, so we test that they work
    annotation = AudioClassificationAnnotation(
        frame=-1000,  # Negative frames are allowed
        name="test",
        value=Text(answer="test")
    )
    assert annotation.frame == -1000


def test_audio_annotation_extra_fields():
    """Test audio annotations can have extra metadata"""
    extra_data = {"source": "automatic", "confidence_score": 0.95}
    
    annotation = AudioClassificationAnnotation(
        frame=3000,
        name="quality",
        value=Text(answer="good"),
        extra=extra_data
    )
    
    assert annotation.extra["source"] == "automatic"
    assert annotation.extra["confidence_score"] == 0.95


def test_audio_annotation_feature_schema():
    """Test audio annotations with feature schema IDs"""
    annotation = AudioClassificationAnnotation(
        frame=4000,
        name="language",
        value=Radio(answer=ClassificationAnswer(name="spanish")),
        feature_schema_id="1234567890123456789012345" # Exactly 25 characters
    )
    
    assert annotation.feature_schema_id == "1234567890123456789012345"


def test_audio_annotation_mixed_types():
    """Test label with mixed audio, video, and image annotations"""
    # Audio annotation
    audio_annotation = AudioClassificationAnnotation(
        frame=2000,
        name="speaker",
        value=Radio(answer=ClassificationAnswer(name="john"))
    )
    
    # Video annotation
    video_annotation = lb_types.VideoClassificationAnnotation(
        frame=10,
        name="quality",
        value=Text(answer="good")
    )
    
    # Image annotation
    image_annotation = lb_types.ObjectAnnotation(
        name="bbox",
        value=lb_types.Rectangle(
            start=lb_types.Point(x=0, y=0),
            end=lb_types.Point(x=100, y=100)
        )
    )
    
    # Create label with mixed types
    label = lb_types.Label(
        data={"global_key": "mixed_media"},
        annotations=[audio_annotation, video_annotation, image_annotation]
    )
    
    # Test audio-specific method
    audio_frames = label.audio_annotations_by_frame()
    assert 2000 in audio_frames
    assert len(audio_frames[2000]) == 1
    
    # Test video-specific method (should still work)
    video_frames = label.frame_annotations()
    assert 10 in video_frames
    assert len(video_frames[10]) == 1
    
    # Test general object annotations (should still work)
    object_annotations = label.object_annotations()
    assert len(object_annotations) == 1
    assert object_annotations[0].name == "bbox"


def test_audio_annotation_serialization():
    """Test audio annotations can be serialized to dict"""
    annotation = AudioClassificationAnnotation(
        frame=6000,
        name="emotion",
        value=Radio(answer=ClassificationAnswer(name="happy")),
        segment_index=3,
        extra={"confidence": 0.9}
    )
    
    # Test model_dump
    serialized = annotation.model_dump()
    assert serialized["frame"] == 6000
    assert serialized["name"] == "emotion"
    assert serialized["segment_index"] == 3
    assert serialized["extra"]["confidence"] == 0.9
    
    # Test model_dump with exclusions
    serialized_excluded = annotation.model_dump(exclude_none=True)
    assert "frame" in serialized_excluded
    assert "name" in serialized_excluded
    assert "segment_index" in serialized_excluded


def test_audio_annotation_from_dict():
    """Test audio annotations can be created from dict"""
    annotation_data = {
        "frame": 7000,
        "name": "topic",
        "value": Text(answer="technology"),
        "segment_index": 2,
        "extra": {"source": "manual"}
    }
    
    annotation = AudioClassificationAnnotation(**annotation_data)
    
    assert annotation.frame == 7000
    assert annotation.name == "topic"
    assert annotation.segment_index == 2
    assert annotation.extra["source"] == "manual"


def test_audio_annotation_edge_cases():
    """Test audio annotation edge cases"""
    # Test very long audio (many hours)
    long_annotation = AudioClassificationAnnotation.from_time_range(
        start_sec=3600.0,  # 1 hour
        end_sec=7200.0,    # 2 hours
        name="long_audio",
        value=Text(answer="very long")
    )
    
    assert long_annotation.frame == 3600000  # 1 hour in milliseconds
    assert long_annotation.start_time == 3600.0
    
    # Test very short audio (milliseconds)
    short_annotation = AudioClassificationAnnotation.from_time_range(
        start_sec=0.001,  # 1 millisecond
        end_sec=0.002,    # 2 milliseconds
        name="short_audio",
        value=Text(answer="very short")
    )
    
    assert short_annotation.frame == 1  # 1 millisecond
    assert short_annotation.start_time == 0.001
    
    # Test zero time
    zero_annotation = AudioClassificationAnnotation.from_time_range(
        start_sec=0.0,
        end_sec=0.0,
        name="zero_time",
        value=Text(answer="zero")
    )
    
    assert zero_annotation.frame == 0
    assert zero_annotation.start_time == 0.0
