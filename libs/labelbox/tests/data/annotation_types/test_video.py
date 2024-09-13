import labelbox.types as lb_types


def test_mask_frame():
    mask_frame = lb_types.MaskFrame(
        index=1, instance_uri="http://path/to/frame.png"
    )
    assert mask_frame.model_dump(by_alias=True) == {
        "index": 1,
        "imBytes": None,
        "instanceURI": "http://path/to/frame.png",
    }


def test_mask_instance():
    mask_instance = lb_types.MaskInstance(color_rgb=(0, 0, 255), name="mask1")
    assert mask_instance.model_dump(by_alias=True, exclude_none=True) == {
        "colorRGB": (0, 0, 255),
        "name": "mask1",
    }
