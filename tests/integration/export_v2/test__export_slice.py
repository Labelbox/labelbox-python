import pytest


@pytest.mark.skip(
    'Skipping until we have a way to create slices programatically')
def test_export_v2_slice(client):
    # Since we don't have CRUD for slices, we'll just use the one that's already there
    SLICE_ID = "clk04g1e4000ryb0rgsvy1dty"
    slice = client.get_catalog_slice(SLICE_ID)
    task = slice.export_v2(params={
        "performance_details": False,
        "label_details": True
    })
    task.wait_till_done()
    assert task.status == "COMPLETE"
    assert task.errors is None
    assert len(task.result) != 0
