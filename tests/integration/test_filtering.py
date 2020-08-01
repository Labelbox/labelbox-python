import pytest

from labelbox import Project
from labelbox.exceptions import InvalidQueryError


def test_where(client):
    p_a = client.create_project(name="a")
    p_b = client.create_project(name="b")
    p_c = client.create_project(name="c")

    def _get(f, where=None):
        date_where = Project.created_at >= p_a.created_at
        where = date_where if where is None else where & date_where
        return {p.uid for p in client.get_projects(where)}

    def get(where=None):
        return _get(client.get_projects, where)

    assert get() == {p_a.uid, p_b.uid, p_c.uid}
    assert get(Project.name == "a") == {p_a.uid}
    assert get(Project.name != "b") == {p_a.uid, p_c.uid}
    assert get(Project.name > "b") == {p_c.uid}
    assert get(Project.name < "b") == {p_a.uid}
    assert get(Project.name >= "b") == {p_b.uid, p_c.uid}
    assert get(Project.name <= "b") == {p_a.uid, p_b.uid}

    dataset = client.create_dataset(name="Dataset")
    p_a.datasets.connect(dataset)
    p_b.datasets.connect(dataset)
    p_c.datasets.connect(dataset)

    def get(where=None):
        return _get(dataset.projects, where)

    assert get() == {p_a.uid, p_b.uid, p_c.uid}
    assert get(Project.name == "a") == {p_a.uid}
    assert get(Project.name != "b") == {p_a.uid, p_c.uid}
    assert get(Project.name > "b") == {p_c.uid}
    assert get(Project.name < "b") == {p_a.uid}
    assert get(Project.name >= "b") == {p_b.uid, p_c.uid}
    assert get(Project.name <= "b") == {p_a.uid, p_b.uid}

    dataset.delete()
    p_a.delete()
    p_b.delete()
    p_c.delete()


def test_unsupported_where(client):
    with pytest.raises(InvalidQueryError):
        client.get_projects(where=(Project.name == "a") & (Project.name == "b"))

    # TODO support logical OR and NOT in where
    with pytest.raises(InvalidQueryError):
        client.get_projects(where=(Project.name == "a") |
                            (Project.description == "b"))

    with pytest.raises(InvalidQueryError):
        client.get_projects(where=~(Project.name == "a"))
