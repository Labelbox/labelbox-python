import pytest

from labelbox import Project
from labelbox.schema.media_type import MediaType
from labelbox.schema.queue_mode import QueueMode


@pytest.mark.xfail(reason="Relationship sorting not implemented correctly "
                   "on the server-side")
def test_relationship_sorting(client):
    a = client.create_project(name="a",
                              description="b",
                              queue_mode=QueueMode.Batch,
                              media_type=MediaType.Image)
    b = client.create_project(name="b",
                              description="c",
                              queue_mode=QueueMode.Batch,
                              media_type=MediaType.Image)
    c = client.create_project(name="c",
                              description="a",
                              queue_mode=QueueMode.Batch,
                              media_type=MediaType.Image)

    dataset = client.create_dataset(name="Dataset")
    a.datasets.connect(dataset)
    b.datasets.connect(dataset)
    c.datasets.connect(dataset)

    def get(order_by):
        where = Project.created_at >= a.created_at
        return list(dataset.projects(where=where, order_by=order_by))

    assert get(Project.name.asc) == [a, b, c]
    assert get(Project.name.desc) == [c, b, a]
    assert get(Project.description.asc) == [c, a, b]
    assert get(Project.description.desc) == [b, a, c]

    dataset.delete()
    a.delete()
    b.delete()
    c.delete()


@pytest.mark.xfail(reason="Sorting not supported on top-level fetches")
def test_top_level_sorting(client):
    client.get_projects(order_by=Project.name.asc)
