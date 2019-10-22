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


def test_project_filtering(client, rand_gen):
    name_1 = rand_gen(str)
    name_2 = rand_gen(str)
    p1 = client.create_project(name=name_1)
    p2 = client.create_project(name=name_2)

    assert list(client.get_projects(where=Project.name==name_1)) == [p1]
    assert list(client.get_projects(where=Project.name==name_2)) == [p2]

    p1.delete()
    p2.delete()


def test_upsert_review_queue(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    project.upsert_review_queue(0.6)
    project.delete()
