from labelbox import Project


def test_project(client, rand_gen):
    before = list(client.get_projects())
    for o in before:
        assert isinstance(o, Project)

    data = {"name": rand_gen(str), "description": rand_gen(str)}
    project = client.create_project(**data)
    assert project.name == data["name"]
    assert project.description == data["description"]

    after = list(client.get_projects())
    assert len(after) == len(before) + 1
    assert project in after

    project = client.get_project(project.uid)
    assert project.name == data["name"]
    assert project.description == data["description"]

    update_data = {"name": rand_gen(str), "description": rand_gen(str)}
    project.update(**update_data)
    # Test local object updates.
    assert project.name == update_data["name"]
    assert project.description == update_data["description"]

    # Test remote updates.
    project = client.get_project(project.uid)
    assert project.name == update_data["name"]
    assert project.description == update_data["description"]

    project.delete()
    final = list(client.get_projects())
    assert project not in final
    assert set(final) == set(before)

    # TODO this should raise ResourceNotFoundError, but it doesn't
    project = client.get_project(project.uid)


def test_project_filtering(client):
    p1 = client.create_project(name="p1")
    p2 = client.create_project(name="p2")

    assert list(client.get_projects(where=Project.name=="p1")) == [p1]
    assert list(client.get_projects(where=Project.name=="p2")) == [p2]

    p1.delete()
    p2.delete()
