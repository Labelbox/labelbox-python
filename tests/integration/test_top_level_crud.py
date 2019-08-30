import pytest

from labelbox.client import Project, Dataset


def create_update_delete(db_object_type, get_all_f, get_single_f, create_f,
                         fields, rand_gen):
    before = list(get_all_f())
    return
    for o in before:
        assert isinstance(o, db_object_type)

    data = {field.name: gen(field) for field, gen in fields.items()}
    obj = create(**data)

    # Test that the created object has values set
    for field, value in data:
        assert getattr(obj, field.name) == value

    # Test the created object is returned in the new fetch
    after = list(get_all_f())
    assert len(after) == len(before) + 1
    assert obj.uid in {o.uid for o in after}

    # Test fetch on ID
    if get_single_f:
        obj_2 = get_single_f(obj.uid)
        for field, value in data:
            assert getattr(obj_2, field.name) == value

    # Test data update
    update_data = {field.name: gen() for field, gen in fields.items()}
    assert update_data != data
    obj.update(**update_data)
    # Test that the local object is updated
    for field, value in update_data:
        assert getattr(obj_updated, field.name) == value
    # Test that the server-side is updated
    obj = get_all_f(where=db_object_type.uid == obj.uid)
    for field, value in update_data:
        assert getattr(obj_updated, field.name) == value

    # Test delete
    obj.delete()
    final = list(get_all_f())
    assert len(final) == len(before)
    assert obj.uid not in {o.uid for o in final}

    if get_single_f:
        with pytest.raises(ResourceNotFoundError):
            get_single_f(obj.uid)


def test_crud_project(client, rand_gen):
    create_update_delete(
        Project, client.get_projects, client.get_project, client.create_project,
        (Project.name, Project.description), rand_gen)


def test_crud_dataset(client, rand_gen):
    create_update_delete(
        Dataset, client.get_datasets, client.get_dataset, client.create_dataset,
        [Dataset.name], rand_gen)
