import pytest

from labelbox import Project
from labelbox.exceptions import InvalidAttributeError


def test_update(client, rand_gen):
    name_1 = rand_gen(str)
    assert len(list(client.get_projects(where=Project.name == name_1))) == 0
    project = client.create_project(name=name_1)
    assert project.name == name_1
    assert len(list(client.get_projects(where=Project.name == name_1))) == 1

    name_2 = rand_gen(str)
    assert name_2 != name_1
    project.update(name=name_2)
    assert project.name == name_2
    assert len(list(client.get_projects(where=Project.name == name_1))) == 0
    assert len(list(client.get_projects(where=Project.name == name_2))) == 1

    with pytest.raises(InvalidAttributeError) as excinfo:
        project.update(invalid_project_attribute=42)
    assert excinfo.value.db_object_type == Project
    assert excinfo.value.field == "invalid_project_attribute"
