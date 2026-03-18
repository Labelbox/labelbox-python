"""Position models for issues, varying by media type.

Each position model serializes to a GeoJSON-compatible dict for the
``position: Json`` GraphQL field.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, field_validator

from labelbox.schema.media_type import MediaType

logger = logging.getLogger(__name__)


class ImageIssuePosition(BaseModel):
    """Pin position on an image asset.

    Attributes:
        x: Horizontal pixel coordinate.
        y: Vertical pixel coordinate.
    """

    x: int
    y: int

    def to_dict(self) -> dict:
        return {"type": "Point", "coordinates": [self.x, self.y]}


class PdfIssuePosition(BaseModel):
    """Pin position on a PDF page.

    Coordinates are expressed as percentages (0.0 – 1.0) of the page
    dimensions, matching the backend ``PERCENT`` unit.

    Attributes:
        x: Horizontal position as a fraction of page width (0.0 – 1.0).
        y: Vertical position as a fraction of page height (0.0 – 1.0).
        page: Zero-based page index.
    """

    x: float
    y: float
    page: int

    @field_validator("x", "y")
    @classmethod
    def _check_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(
                "PDF coordinates must be between 0.0 and 1.0 (percentage). "
                f"Got {v}."
            )
        return v

    def to_dict(self) -> dict:
        return {
            "type": "Point",
            "coordinates": [self.x, self.y],
            "page": self.page,
            "unit": "PERCENT",
        }


class TextIssuePosition(BaseModel):
    """Character range within a text block.

    Attributes:
        text_block_id: Identifier of the text block.
        start_char_index: Start character index (inclusive).
        end_char_index: End character index (exclusive).
    """

    text_block_id: str
    start_char_index: int
    end_char_index: int

    def to_dict(self) -> dict:
        return {
            "textBlockId": self.text_block_id,
            "startCharIndex": self.start_char_index,
            "endCharIndex": self.end_char_index,
        }


class VideoFrameRange(BaseModel):
    """A contiguous frame range with optional moving coordinates.

    For a single frame, set ``start == end``.  When ``start == end`` the
    ``end_x`` / ``end_y`` fields are ignored during serialization.

    Attributes:
        start: Start frame number.
        end: End frame number (equal to *start* for a single frame).
        x: Horizontal pixel coordinate at *start*.
        y: Vertical pixel coordinate at *start*.
        end_x: Horizontal pixel coordinate at *end* (moving pin). Ignored
            when ``start == end``.
        end_y: Vertical pixel coordinate at *end* (moving pin). Ignored
            when ``start == end``.
    """

    start: int
    end: int
    x: int
    y: int
    end_x: Optional[int] = None
    end_y: Optional[int] = None


class VideoIssuePosition(BaseModel):
    """Pin position(s) on a video asset.

    Supports single frames, contiguous ranges, and multiple separated
    ranges (with optional moving coordinates).

    Attributes:
        frames: One or more :class:`VideoFrameRange` entries.
    """

    frames: List[VideoFrameRange]

    def to_dict(self) -> dict:
        """Serialize to KeyframesGeoJSONPoint format."""
        keyframes: list = []
        for fr in self.frames:
            start_entry = {
                "frame": fr.start,
                "value": {
                    "type": "Point",
                    "coordinates": [fr.x, fr.y],
                },
            }
            keyframes.append(start_entry)
            # Only emit a separate end keyframe when the range spans
            # multiple frames.
            if fr.end != fr.start:
                end_entry = {
                    "frame": fr.end,
                    "value": {
                        "type": "Point",
                        "coordinates": [
                            fr.end_x if fr.end_x is not None else fr.x,
                            fr.end_y if fr.end_y is not None else fr.y,
                        ],
                    },
                }
                keyframes.append(end_entry)
        return {"type": "KeyframesGeoJSONPoint", "keyframes": keyframes}


IssuePosition = Union[
    ImageIssuePosition,
    PdfIssuePosition,
    TextIssuePosition,
    VideoIssuePosition,
]

MEDIA_TYPE_POSITION_MAP: Dict[MediaType, type] = {
    MediaType.Image: ImageIssuePosition,
    MediaType.Video: VideoIssuePosition,
    MediaType.Text: TextIssuePosition,
    MediaType.Document: PdfIssuePosition,
    MediaType.Pdf: PdfIssuePosition,
}


def _deserialize_position(
    raw: Optional[Union[str, dict]],
) -> Optional[IssuePosition]:
    """Convert a raw position value from GraphQL into a typed model.

    Returns ``None`` (with a warning) when the structure is unrecognized,
    ensuring forward-compatibility with new media types.
    """
    if raw is None:
        return None

    data: Any  # Use Any for safer checking after json.loads
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            if data is None:
                return None
        except (json.JSONDecodeError, TypeError):
            return None
    else:
        data = raw

    if not isinstance(data, dict):
        return None

    try:
        # PDF – has "page" key
        if "page" in data:
            coords = data.get("coordinates", [0.0, 0.0])
            return PdfIssuePosition(x=coords[0], y=coords[1], page=data["page"])

        # Text – has "textBlockId" key
        if "textBlockId" in data:
            return TextIssuePosition(
                text_block_id=data["textBlockId"],
                start_char_index=data["startCharIndex"],
                end_char_index=data["endCharIndex"],
            )

        # Video – KeyframesGeoJSONPoint
        if data.get("type") == "KeyframesGeoJSONPoint":
            frames: List[VideoFrameRange] = []
            kf_list = data.get("keyframes", [])
            i = 0
            while i < len(kf_list):
                kf = kf_list[i]
                start_frame = kf["frame"]
                start_coords = kf["value"]["coordinates"]
                # Look ahead for an end keyframe
                if i + 1 < len(kf_list):
                    next_kf = kf_list[i + 1]
                    next_coords = next_kf["value"]["coordinates"]
                    end_frame = next_kf["frame"]
                    if end_frame != start_frame:
                        frames.append(
                            VideoFrameRange(
                                start=start_frame,
                                end=end_frame,
                                x=int(start_coords[0]),
                                y=int(start_coords[1]),
                                end_x=int(next_coords[0]),
                                end_y=int(next_coords[1]),
                            )
                        )
                        i += 2
                        continue
                # Single frame or last entry
                frames.append(
                    VideoFrameRange(
                        start=start_frame,
                        end=start_frame,
                        x=int(start_coords[0]),
                        y=int(start_coords[1]),
                    )
                )
                i += 1
            return VideoIssuePosition(frames=frames)

        # Image – plain GeoJSON Point
        if data.get("type") == "Point":
            coords = data.get("coordinates", [0, 0])
            return ImageIssuePosition(x=int(coords[0]), y=int(coords[1]))
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning(
            "Failed to deserialize issue position: %s (%s)", data, exc
        )
        return None

    logger.warning("Unrecognized issue position structure: %s", data)
    return None
