import logging

import pytest

from labelbox.schema.issue_position import (
    MEDIA_TYPE_POSITION_MAP,
    ImageIssuePosition,
    PdfIssuePosition,
    TextIssuePosition,
    VideoFrameRange,
    VideoIssuePosition,
    _deserialize_position,
)
from labelbox.schema.media_type import MediaType


# ---------------------------------------------------------------------------
# ImageIssuePosition
# ---------------------------------------------------------------------------


class TestImageIssuePosition:
    def test_to_dict(self):
        pos = ImageIssuePosition(x=100, y=200)
        assert pos.to_dict() == {
            "type": "Point",
            "coordinates": [100, 200],
        }

    def test_integer_coordinates(self):
        pos = ImageIssuePosition(x=0, y=0)
        assert isinstance(pos.x, int)
        assert isinstance(pos.y, int)


# ---------------------------------------------------------------------------
# PdfIssuePosition
# ---------------------------------------------------------------------------


class TestPdfIssuePosition:
    def test_to_dict(self):
        pos = PdfIssuePosition(x=0.5, y=0.75, page=2)
        assert pos.to_dict() == {
            "type": "Point",
            "coordinates": [0.5, 0.75],
            "page": 2,
            "unit": "PERCENT",
        }

    def test_validation_x_out_of_range(self):
        with pytest.raises(ValueError, match="0.0 and 1.0"):
            PdfIssuePosition(x=1.5, y=0.5, page=0)

    def test_validation_y_out_of_range(self):
        with pytest.raises(ValueError, match="0.0 and 1.0"):
            PdfIssuePosition(x=0.5, y=-0.1, page=0)

    def test_boundary_values(self):
        pos_min = PdfIssuePosition(x=0.0, y=0.0, page=0)
        assert pos_min.x == 0.0
        pos_max = PdfIssuePosition(x=1.0, y=1.0, page=0)
        assert pos_max.x == 1.0


# ---------------------------------------------------------------------------
# TextIssuePosition
# ---------------------------------------------------------------------------


class TestTextIssuePosition:
    def test_to_dict(self):
        pos = TextIssuePosition(
            text_block_id="block-1",
            start_char_index=10,
            end_char_index=25,
        )
        assert pos.to_dict() == {
            "textBlockId": "block-1",
            "startCharIndex": 10,
            "endCharIndex": 25,
        }


# ---------------------------------------------------------------------------
# VideoIssuePosition
# ---------------------------------------------------------------------------


class TestVideoIssuePosition:
    def test_single_frame(self):
        pos = VideoIssuePosition(
            frames=[VideoFrameRange(start=5, end=5, x=100, y=200)]
        )
        result = pos.to_dict()
        assert result["type"] == "KeyframesGeoJSONPoint"
        assert len(result["keyframes"]) == 1
        kf = result["keyframes"][0]
        assert kf["frame"] == 5
        assert kf["value"]["coordinates"] == [100, 200]

    def test_contiguous_range(self):
        pos = VideoIssuePosition(
            frames=[VideoFrameRange(start=5, end=11, x=450, y=300)]
        )
        result = pos.to_dict()
        assert len(result["keyframes"]) == 2
        assert result["keyframes"][0]["frame"] == 5
        assert result["keyframes"][1]["frame"] == 11
        # No end_x/end_y => coordinates repeat
        assert result["keyframes"][1]["value"]["coordinates"] == [450, 300]

    def test_moving_coordinates(self):
        pos = VideoIssuePosition(
            frames=[
                VideoFrameRange(
                    start=5, end=11, x=450, y=300, end_x=500, end_y=350
                )
            ]
        )
        result = pos.to_dict()
        assert len(result["keyframes"]) == 2
        assert result["keyframes"][0]["value"]["coordinates"] == [450, 300]
        assert result["keyframes"][1]["value"]["coordinates"] == [500, 350]

    def test_multiple_ranges(self):
        pos = VideoIssuePosition(
            frames=[
                VideoFrameRange(start=5, end=11, x=450, y=300),
                VideoFrameRange(start=20, end=25, x=100, y=100),
            ]
        )
        result = pos.to_dict()
        assert len(result["keyframes"]) == 4

    def test_single_frame_ignores_end_coords(self):
        """When start == end, end_x/end_y are not serialized."""
        pos = VideoIssuePosition(
            frames=[
                VideoFrameRange(
                    start=5, end=5, x=100, y=200, end_x=999, end_y=999
                )
            ]
        )
        result = pos.to_dict()
        assert len(result["keyframes"]) == 1
        assert result["keyframes"][0]["value"]["coordinates"] == [100, 200]


# ---------------------------------------------------------------------------
# MEDIA_TYPE_POSITION_MAP
# ---------------------------------------------------------------------------


class TestMediaTypePositionMap:
    def test_image(self):
        assert MEDIA_TYPE_POSITION_MAP[MediaType.Image] is ImageIssuePosition

    def test_video(self):
        assert MEDIA_TYPE_POSITION_MAP[MediaType.Video] is VideoIssuePosition

    def test_text(self):
        assert MEDIA_TYPE_POSITION_MAP[MediaType.Text] is TextIssuePosition

    def test_document(self):
        assert MEDIA_TYPE_POSITION_MAP[MediaType.Document] is PdfIssuePosition

    def test_pdf(self):
        assert MEDIA_TYPE_POSITION_MAP[MediaType.Pdf] is PdfIssuePosition

    def test_audio_not_in_map(self):
        assert MediaType.Audio not in MEDIA_TYPE_POSITION_MAP


# ---------------------------------------------------------------------------
# _deserialize_position
# ---------------------------------------------------------------------------


class TestDeserializePosition:
    def test_none_input(self):
        assert _deserialize_position(None) is None

    def test_image_geojson(self):
        raw = {"type": "Point", "coordinates": [100, 200]}
        result = _deserialize_position(raw)
        assert isinstance(result, ImageIssuePosition)
        assert result.x == 100
        assert result.y == 200

    def test_pdf_geojson(self):
        raw = {
            "type": "Point",
            "coordinates": [0.5, 0.75],
            "page": 2,
            "unit": "PERCENT",
        }
        result = _deserialize_position(raw)
        assert isinstance(result, PdfIssuePosition)
        assert result.page == 2

    def test_text_position(self):
        raw = {
            "textBlockId": "block-1",
            "startCharIndex": 10,
            "endCharIndex": 25,
        }
        result = _deserialize_position(raw)
        assert isinstance(result, TextIssuePosition)
        assert result.text_block_id == "block-1"

    def test_video_position(self):
        raw = {
            "type": "KeyframesGeoJSONPoint",
            "keyframes": [
                {
                    "frame": 5,
                    "value": {"type": "Point", "coordinates": [100, 200]},
                },
                {
                    "frame": 11,
                    "value": {"type": "Point", "coordinates": [150, 250]},
                },
            ],
        }
        result = _deserialize_position(raw)
        assert isinstance(result, VideoIssuePosition)
        assert len(result.frames) == 1
        assert result.frames[0].start == 5
        assert result.frames[0].end == 11

    def test_json_string_input(self):
        import json

        raw = json.dumps({"type": "Point", "coordinates": [10, 20]})
        result = _deserialize_position(raw)
        assert isinstance(result, ImageIssuePosition)
        assert result.x == 10

    def test_unrecognized_structure_returns_none(self, caplog):
        raw = {"unknown_key": "some_value"}
        with caplog.at_level(logging.WARNING):
            result = _deserialize_position(raw)
        assert result is None
        assert "Unrecognized issue position structure" in caplog.text

    def test_invalid_json_string_returns_none(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = _deserialize_position("not-valid-json")
        assert result is None
