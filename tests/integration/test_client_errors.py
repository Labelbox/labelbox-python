from multiprocessing.dummy import Pool
import os
import time

import pytest

from labelbox import Project, Dataset, User
import labelbox.client
import labelbox.exceptions


def test_missing_api_key(client):
    key = os.environ.get(labelbox.client._LABELBOX_API_KEY, None)
    if key is not None:
        del os.environ[labelbox.client._LABELBOX_API_KEY]

    with pytest.raises(labelbox.exceptions.AuthenticationError) as excinfo:
        labelbox.client.Client()

    assert excinfo.value.message == "Labelbox API key not provided"

    if key is not None:
        os.environ[labelbox.client._LABELBOX_API_KEY] = key


def test_bad_key(client, rand_gen):
    bad_key = "BAD_KEY_" + rand_gen(str)
    client = labelbox.client.Client(api_key=bad_key)

    with pytest.raises(labelbox.exceptions.AuthenticationError) as excinfo:
        client.create_project(name=rand_gen(str))


def test_syntax_error(client):
    with pytest.raises(labelbox.exceptions.InvalidQueryError) as excinfo:
        client.execute("asda", check_naming=False)
    assert excinfo.value.message.startswith("Syntax Error:")


def test_semantic_error(client):
    with pytest.raises(labelbox.exceptions.InvalidQueryError) as excinfo:
        client.execute("query {bbb {id}}", check_naming=False)
    assert excinfo.value.message.startswith("Cannot query field \"bbb\"")


def test_timeout_error(client):
    with pytest.raises(labelbox.exceptions.TimeoutError) as excinfo:
        client.execute("{projects {id}}", check_naming=False, timeout=0.001)


def test_query_complexity_error(client):
    with pytest.raises(labelbox.exceptions.ValidationFailedError) as excinfo:
        client.execute("{projects {datasets {dataRows {labels {id}}}}}",
                       check_naming=False)
    assert excinfo.value.message == "Query complexity limit exceeded"


def test_resource_not_found_error(client):
    with pytest.raises(labelbox.exceptions.ResourceNotFoundError):
        client.get_project("invalid project ID")


def test_network_error(client):
    client = labelbox.client.Client(api_key=client.api_key,
                                    endpoint="not_a_valid_URL")

    with pytest.raises(labelbox.exceptions.NetworkError) as excinfo:
        client.create_project(name="Project name")


def test_invalid_attribute_error(client, rand_gen):
    # Creation
    with pytest.raises(labelbox.exceptions.InvalidAttributeError) as excinfo:
        client.create_project(name="Name", invalid_field="Whatever")
    assert excinfo.value.db_object_type == Project
    assert excinfo.value.field == "invalid_field"

    # Update
    project = client.create_project(name=rand_gen(str))
    with pytest.raises(labelbox.exceptions.InvalidAttributeError) as excinfo:
        project.update(invalid_field="Whatever")
    assert excinfo.value.db_object_type == Project
    assert excinfo.value.field == "invalid_field"

    # Relationship expansion filtering
    with pytest.raises(labelbox.exceptions.InvalidAttributeError) as excinfo:
        project.datasets(where=User.email == "email")
    assert excinfo.value.db_object_type == Dataset
    assert excinfo.value.field == {User.email}

    # Relationship order-by
    with pytest.raises(labelbox.exceptions.InvalidAttributeError) as excinfo:
        project.datasets(order_by=User.email.asc)
    assert excinfo.value.db_object_type == Dataset
    assert excinfo.value.field == {User.email}

    # Top-level-fetch
    with pytest.raises(labelbox.exceptions.InvalidAttributeError) as excinfo:
        client.get_projects(where=User.email == "email")
    assert excinfo.value.db_object_type == Project
    assert excinfo.value.field == {User.email}

    project.delete()


@pytest.mark.skip
def test_api_limit_error(client, rand_gen):
    project_id = client.create_project(name=rand_gen(str)).uid

    def get(arg):
        try:
            return client.get_project(project_id)
        except labelbox.exceptions.ApiLimitError as e:
            return e

    with Pool(300) as pool:
        results = pool.map(get, list(range(1000)))

    assert labelbox.exceptions.ApiLimitError in {type(r) for r in results}

    # Sleep at the end of this test to allow other tests to execute.
    time.sleep(60)
