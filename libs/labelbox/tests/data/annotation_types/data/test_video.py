import numpy as np
import pytest

from labelbox.data.annotation_types import VideoData
from pydantic import ValidationError


def test_validate_schema():
    with pytest.raises(ValidationError):
        data = VideoData()


def test_frames():
    data = {
        x: (np.random.random((32, 32, 3)) * 255).astype(np.uint8)
        for x in range(5)
    }
    video_data = VideoData(frames=data)
    for idx, frame in video_data.frame_generator():
        assert idx in data
        assert np.all(frame == data[idx])


def test_file_path():
    path = "tests/integration/media/cat.mp4"
    raster_data = VideoData(file_path=path)

    with pytest.raises(ValueError):
        raster_data[0]

    raster_data.load_frames()
    raster_data[0]

    frame_indices = list(raster_data.frames.keys())
    # 29 frames
    assert set(frame_indices) == set(list(range(28)))


def test_file_url():
    url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4"
    raster_data = VideoData(url=url)

    with pytest.raises(ValueError):
        raster_data[0]

    raster_data.load_frames()
    raster_data[0]

    frame_indices = list(raster_data.frames.keys())
    # 362 frames
    assert set(frame_indices) == set(list(range(361)))


def test_ref():
    external_id = "external_id"
    uid = "uid"
    data = {
        x: (np.random.random((32, 32, 3)) * 255).astype(np.uint8)
        for x in range(5)
    }
    metadata = []
    media_attributes = {}
    data = VideoData(
        frames=data,
        external_id=external_id,
        uid=uid,
        metadata=metadata,
        media_attributes=media_attributes,
    )
    assert data.external_id == external_id
    assert data.uid == uid
    assert data.media_attributes == media_attributes
    assert data.metadata == metadata
