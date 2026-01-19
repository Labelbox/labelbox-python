"""Tests for new temporal classification serialization"""

import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.temporal import (
    create_temporal_ndjson_classifications,
)


def test_temporal_text_simple():
    """Test simple TemporalClassificationText serialization"""
    annotations = [
        lb_types.TemporalClassificationText(
            name="transcription",
            value=[
                (1000, 1100, "Hello"),
                (1500, 2400, "How can I help you?"),
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    assert result[0].name == "transcription"
    assert len(result[0].answer) == 2

    # Check first text value
    answer0 = result[0].answer[0]
    assert answer0["value"] == "Hello"
    assert answer0["frames"] == [{"start": 1000, "end": 1100}]

    # Check second text value
    answer1 = result[0].answer[1]
    assert answer1["value"] == "How can I help you?"
    assert answer1["frames"] == [{"start": 1500, "end": 2400}]


def test_temporal_question_radio():
    """Test TemporalClassificationQuestion with single answer (Radio)"""
    annotations = [
        lb_types.TemporalClassificationQuestion(
            name="speaker",
            value=[
                lb_types.TemporalClassificationAnswer(
                    name="user",
                    frames=[(200, 1600)],
                )
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    assert result[0].name == "speaker"
    assert len(result[0].answer) == 1

    answer = result[0].answer[0]
    assert answer["name"] == "user"
    assert answer["frames"] == [{"start": 200, "end": 1600}]


def test_temporal_question_checklist():
    """Test TemporalClassificationQuestion with multiple answers (Checklist)"""
    annotations = [
        lb_types.TemporalClassificationQuestion(
            name="audio_quality",
            value=[
                lb_types.TemporalClassificationAnswer(
                    name="background_noise",
                    frames=[(0, 1500), (2000, 3000)],
                ),
                lb_types.TemporalClassificationAnswer(
                    name="echo",
                    frames=[(2200, 2900)],
                ),
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    assert result[0].name == "audio_quality"
    assert len(result[0].answer) == 2

    # Check background_noise answer
    bg_noise = next(
        a for a in result[0].answer if a["name"] == "background_noise"
    )
    assert bg_noise["frames"] == [
        {"start": 0, "end": 1500},
        {"start": 2000, "end": 3000},
    ]

    # Check echo answer
    echo = next(a for a in result[0].answer if a["name"] == "echo")
    assert echo["frames"] == [{"start": 2200, "end": 2900}]


def test_temporal_text_nested():
    """Test TemporalClassificationText with nested classifications"""
    annotations = [
        lb_types.TemporalClassificationText(
            name="transcription",
            value=[
                (1600, 2000, "Hello, how can I help you?"),
            ],
            classifications=[
                lb_types.TemporalClassificationText(
                    name="speaker_notes",
                    value=[
                        (1600, 2000, "Polite greeting"),
                    ],
                    classifications=[
                        lb_types.TemporalClassificationText(
                            name="context_tags",
                            value=[
                                (1800, 2000, "customer service tone"),
                            ],
                        )
                    ],
                )
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    assert result[0].name == "transcription"
    assert len(result[0].answer) == 1

    answer = result[0].answer[0]
    assert answer["value"] == "Hello, how can I help you?"
    assert answer["frames"] == [{"start": 1600, "end": 2000}]

    # Check nested classifications
    assert "classifications" in answer
    assert len(answer["classifications"]) == 1

    nested1 = answer["classifications"][0]
    assert nested1["name"] == "speaker_notes"
    assert len(nested1["answer"]) == 1
    assert nested1["answer"][0]["value"] == "Polite greeting"

    # Check deeper nesting
    assert "classifications" in nested1["answer"][0]
    nested2 = nested1["answer"][0]["classifications"][0]
    assert nested2["name"] == "context_tags"
    assert nested2["answer"][0]["value"] == "customer service tone"


def test_temporal_question_nested():
    """Test TemporalClassificationQuestion with nested classifications"""
    annotations = [
        lb_types.TemporalClassificationQuestion(
            name="speaker",
            value=[
                lb_types.TemporalClassificationAnswer(
                    name="user",
                    frames=[(200, 1600)],
                    classifications=[
                        lb_types.TemporalClassificationQuestion(
                            name="tone",
                            value=[
                                lb_types.TemporalClassificationAnswer(
                                    name="professional",
                                    frames=[(1000, 1600)],
                                    classifications=[
                                        lb_types.TemporalClassificationQuestion(
                                            name="clarity",
                                            value=[
                                                lb_types.TemporalClassificationAnswer(
                                                    name="clear",
                                                    frames=[(1300, 1600)],
                                                )
                                            ],
                                        )
                                    ],
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    answer = result[0].answer[0]
    assert answer["name"] == "user"

    # Check nested tone
    assert "classifications" in answer
    tone = answer["classifications"][0]
    assert tone["name"] == "tone"
    assert tone["answer"][0]["name"] == "professional"

    # Check deeper nested clarity
    clarity = tone["answer"][0]["classifications"][0]
    assert clarity["name"] == "clarity"
    assert clarity["answer"][0]["name"] == "clear"
    assert clarity["answer"][0]["frames"] == [{"start": 1300, "end": 1600}]


def test_frame_validation_discard_invalid():
    """Test that invalid frames (not subset of parent) are discarded"""
    annotations = [
        lb_types.TemporalClassificationQuestion(
            name="speaker",
            value=[
                lb_types.TemporalClassificationAnswer(
                    name="user",
                    frames=[(200, 1600)],  # Parent range
                    classifications=[
                        lb_types.TemporalClassificationText(
                            name="notes",
                            value=[
                                (300, 800, "Valid note"),  # Within parent range
                                (
                                    1700,
                                    2000,
                                    "Invalid note",
                                ),  # Outside parent range
                            ],
                        )
                    ],
                )
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    # Find the nested notes classification
    answer = result[0].answer[0]
    notes = answer["classifications"][0]

    # Only the valid note should be present
    assert len(notes["answer"]) == 1
    assert notes["answer"][0]["value"] == "Valid note"
    assert notes["answer"][0]["frames"] == [{"start": 300, "end": 800}]


def test_frame_deduplication():
    """Test that duplicate frames are removed"""
    annotations = [
        lb_types.TemporalClassificationText(
            name="transcription",
            value=[
                (1000, 1100, "Hello"),
                (1000, 1100, "Hello"),  # Duplicate
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    # Should only have one entry
    assert len(result[0].answer) == 1
    assert result[0].answer[0]["frames"] == [{"start": 1000, "end": 1100}]


def test_mixed_text_and_question_nesting():
    """Test Checklist > Text > Radio nesting"""
    annotations = [
        lb_types.TemporalClassificationQuestion(
            name="checklist_class",
            value=[
                lb_types.TemporalClassificationAnswer(
                    name="quality_check",
                    frames=[(1, 1500)],
                    classifications=[
                        lb_types.TemporalClassificationText(
                            name="notes_text",
                            value=[
                                (1, 1500, "Audio quality is excellent"),
                            ],
                            classifications=[
                                lb_types.TemporalClassificationQuestion(
                                    name="severity_radio",
                                    value=[
                                        lb_types.TemporalClassificationAnswer(
                                            name="minor",
                                            frames=[(1, 1500)],
                                        )
                                    ],
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    answer = result[0].answer[0]
    assert answer["name"] == "quality_check"

    # Check text classification
    text_cls = answer["classifications"][0]
    assert text_cls["name"] == "notes_text"
    assert text_cls["answer"][0]["value"] == "Audio quality is excellent"

    # Check radio classification
    radio_cls = text_cls["answer"][0]["classifications"][0]
    assert radio_cls["name"] == "severity_radio"
    assert radio_cls["answer"][0]["name"] == "minor"


def test_inductive_structure_text_with_shared_nested_radio():
    """
    Test inductive structure where multiple text values share the same nested radio classification.

    Each text value should get its own instance of the nested radio with only the radio answers
    that overlap with that text value's frames.
    """
    annotations = [
        lb_types.TemporalClassificationText(
            name="content_notes",
            value=[
                (1000, 1500, "Topic is relevant"),
                (1501, 2000, "Good pacing"),
            ],
            classifications=[
                # Shared nested radio with answers for BOTH text values
                lb_types.TemporalClassificationQuestion(
                    name="clarity_radio",
                    value=[
                        lb_types.TemporalClassificationAnswer(
                            name="very_clear",
                            frames=[(1000, 1500)],
                        ),
                        lb_types.TemporalClassificationAnswer(
                            name="slightly_clear",
                            frames=[(1501, 2000)],
                        ),
                    ],
                )
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    assert result[0].name == "content_notes"
    assert len(result[0].answer) == 2

    # Check first text value: "Topic is relevant"
    text1 = next(
        a for a in result[0].answer if a["value"] == "Topic is relevant"
    )
    assert text1["frames"] == [{"start": 1000, "end": 1500}]
    assert "classifications" in text1
    assert len(text1["classifications"]) == 1

    # Should only have "very_clear" radio answer (overlaps with 1000-1500)
    radio1 = text1["classifications"][0]
    assert radio1["name"] == "clarity_radio"
    assert len(radio1["answer"]) == 1
    assert radio1["answer"][0]["name"] == "very_clear"
    assert radio1["answer"][0]["frames"] == [{"start": 1000, "end": 1500}]

    # Check second text value: "Good pacing"
    text2 = next(a for a in result[0].answer if a["value"] == "Good pacing")
    assert text2["frames"] == [{"start": 1501, "end": 2000}]
    assert "classifications" in text2
    assert len(text2["classifications"]) == 1

    # Should only have "slightly_clear" radio answer (overlaps with 1501-2000)
    radio2 = text2["classifications"][0]
    assert radio2["name"] == "clarity_radio"
    assert len(radio2["answer"]) == 1
    assert radio2["answer"][0]["name"] == "slightly_clear"
    assert radio2["answer"][0]["frames"] == [{"start": 1501, "end": 2000}]


def test_inductive_structure_checklist_with_multiple_text_values():
    """
    Test inductive structure with Checklist > Text > Radio where text has multiple values
    and nested radio has answers that map to different text values.
    """
    annotations = [
        lb_types.TemporalClassificationQuestion(
            name="checklist_class",
            value=[
                lb_types.TemporalClassificationAnswer(
                    name="content_check",
                    frames=[(1000, 2000)],
                    classifications=[
                        lb_types.TemporalClassificationText(
                            name="content_notes_text",
                            value=[
                                (1000, 1500, "Topic is relevant"),
                                (1501, 2000, "Good pacing"),
                            ],
                            classifications=[
                                # Nested radio with multiple answers covering different text value frames
                                lb_types.TemporalClassificationQuestion(
                                    name="clarity_radio",
                                    value=[
                                        lb_types.TemporalClassificationAnswer(
                                            name="very_clear",
                                            frames=[(1000, 1500)],
                                        ),
                                        lb_types.TemporalClassificationAnswer(
                                            name="slightly_clear",
                                            frames=[(1501, 2000)],
                                        ),
                                    ],
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    ]

    result = create_temporal_ndjson_classifications(
        annotations, "test-global-key"
    )

    assert len(result) == 1
    assert result[0].name == "checklist_class"

    # Get the content_check answer
    content_check = result[0].answer[0]
    assert content_check["name"] == "content_check"
    assert content_check["frames"] == [{"start": 1000, "end": 2000}]

    # Get the nested text classification
    text_cls = content_check["classifications"][0]
    assert text_cls["name"] == "content_notes_text"
    assert len(text_cls["answer"]) == 2

    # Check first text value and its nested radio
    text1 = next(
        a for a in text_cls["answer"] if a["value"] == "Topic is relevant"
    )
    assert text1["frames"] == [{"start": 1000, "end": 1500}]
    radio1 = text1["classifications"][0]
    assert radio1["name"] == "clarity_radio"
    assert len(radio1["answer"]) == 1
    assert radio1["answer"][0]["name"] == "very_clear"

    # Check second text value and its nested radio
    text2 = next(a for a in text_cls["answer"] if a["value"] == "Good pacing")
    assert text2["frames"] == [{"start": 1501, "end": 2000}]
    radio2 = text2["classifications"][0]
    assert radio2["name"] == "clarity_radio"
    assert len(radio2["answer"]) == 1
    assert radio2["answer"][0]["name"] == "slightly_clear"
