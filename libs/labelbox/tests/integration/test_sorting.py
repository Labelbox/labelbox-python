import pytest

from labelbox import Project


@pytest.mark.xfail(reason="Sorting not supported on top-level fetches")
def test_top_level_sorting(client):
    client.get_projects(order_by=Project.name.asc)
