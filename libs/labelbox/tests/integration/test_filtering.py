import pytest

from labelbox import Project
from labelbox.exceptions import InvalidQueryError
from labelbox.schema.queue_mode import QueueMode


@pytest.fixture
def project_to_test_where(client, rand_gen):
    p_a_name = f"a-{rand_gen(str)}"
    p_b_name = f"b-{rand_gen(str)}"
    p_c_name = f"c-{rand_gen(str)}"

    p_a = client.create_project(name=p_a_name, queue_mode=QueueMode.Batch)
    p_b = client.create_project(name=p_b_name, queue_mode=QueueMode.Batch)
    p_c = client.create_project(name=p_c_name, queue_mode=QueueMode.Batch)

    yield p_a, p_b, p_c

    p_a.delete()
    p_b.delete()
    p_c.delete()


# Avoid assertions using equality to prevent intermittent failures due to
# other builds simultaneously adding projects to test org
def test_where(client, project_to_test_where):
    p_a, p_b, p_c = project_to_test_where
    p_a_name = p_a.name
    p_b_name = p_b.name

    def get(where=None):
        date_where = Project.created_at >= p_a.created_at
        where = date_where if where is None else where & date_where
        return {p.uid for p in client.get_projects(where)}

    assert {p_a.uid, p_b.uid, p_c.uid}.issubset(get())
    e_a = get(Project.name == p_a_name)
    assert p_a.uid in e_a and p_b.uid not in e_a and p_c.uid not in e_a
    not_b = get(Project.name != p_b_name)
    assert {p_a.uid, p_c.uid}.issubset(not_b) and p_b.uid not in not_b
    gt_b = get(Project.name > p_b_name)
    assert p_c.uid in gt_b and p_a.uid not in gt_b and p_b.uid not in gt_b
    lt_b = get(Project.name < p_b_name)
    assert p_a.uid in lt_b and p_b.uid not in lt_b and p_c.uid not in lt_b
    ge_b = get(Project.name >= p_b_name)
    assert {p_b.uid, p_c.uid}.issubset(ge_b) and p_a.uid not in ge_b
    le_b = get(Project.name <= p_b_name)
    assert {p_a.uid, p_b.uid}.issubset(le_b) and p_c.uid not in le_b


def test_unsupported_where(client):
    with pytest.raises(InvalidQueryError):
        client.get_projects(where=(Project.name == "a") & (Project.name == "b"))

    # TODO support logical OR and NOT in where
    with pytest.raises(InvalidQueryError):
        client.get_projects(where=(Project.name == "a") |
                            (Project.description == "b"))

    with pytest.raises(InvalidQueryError):
        client.get_projects(where=~(Project.name == "a"))
