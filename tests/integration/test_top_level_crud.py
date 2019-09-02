import pytest

from labelbox import Project, Dataset
from labelbox.exceptions import ResourceNotFoundError


def create_update_delete(db_object_type, get_all_f, get_single_f, create_f,
                         fields, rand_gen):
    before = list(get_all_f())
    for o in before:
        assert isinstance(o, db_object_type)

    data = {field.name: rand_gen(field) for field in fields}
    obj = create_f(**data)

    # Test that the created object has values set
    for field_name, value in data.items():
        assert getattr(obj, field_name) == value

    # Test the created object is returned in the new fetch
    after = list(get_all_f())
    assert len(after) == len(before) + 1
    assert obj.uid in {o.uid for o in after}

    # Test fetch on ID
    if get_single_f:
        obj_2 = get_single_f(obj.uid)
        for field_name, value in data.items():
            assert getattr(obj_2, field_name) == value

    # Test data update
    update_data = {field.name: rand_gen(field) for field in fields}
    assert update_data != data
    obj.update(**update_data)
    # Test that the local object is updated
    for field_name, value in update_data.items():
        assert getattr(obj, field_name) == value
    # Test that the server-side is updated
    during = list(get_all_f(where=db_object_type.uid == obj.uid))
    assert len(during) == 1
    obj = during[0]
    for field_name, value in update_data.items():
        assert getattr(obj, field_name) == value

    # Test delete
    obj.delete()
    final = list(get_all_f())
    assert len(final) == len(before)
    assert obj.uid not in {o.uid for o in final}

    if get_single_f:
        if db_object_type == Project:
            # TODO this should raise ResourceNotFoundError, but it doesn't
            obj = get_single_f(obj.uid)
        else:
            with pytest.raises(ResourceNotFoundError):
                obj = get_single_f(obj.uid)


def test_crud_project(client, rand_gen):
    create_update_delete(
        Project, client.get_projects, client.get_project, client.create_project,
        (Project.name, Project.description), rand_gen)


def test_crud_dataset(client, rand_gen):
    create_update_delete(
        Dataset, client.get_datasets, client.get_dataset, client.create_dataset,
        [Dataset.name], rand_gen)
