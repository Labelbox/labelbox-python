import pytest

from labelbox import Project


@pytest.mark.skip
def test_relationship_sorting(client):
    a = client.create_project(name="a", description="b")
    b = client.create_project(name="b", description="c")
    c = client.create_project(name="c", description="a")

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


def test_top_level_sorting(client):
    # TODO support sorting on top-level fetches
    with pytest.raises(TypeError):
        client.get_projects(order_by=Project.name.asc)
