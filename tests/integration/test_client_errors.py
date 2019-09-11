from multiprocessing.dummy import Pool
import os
import time

import pytest

import labelbox.client
import labelbox.exceptions


def test_missing_api_key(client, rand_gen):
    key = os.environ.get(labelbox.client._LABELBOX_API_KEY, None)
    del os.environ[labelbox.client._LABELBOX_API_KEY]

    with pytest.raises(labelbox.exceptions.AuthenticationError) as excinfo:
        labelbox.client.Client()

    assert excinfo.value.message == "Labelbox API key not provided"

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


def test_api_limit_error(client, rand_gen):
    project_id = client.create_project(name=rand_gen(str)).uid

    def get(arg):
        try:
            return client.get_project(project_id)
        except Exception as e:
            return e

    with Pool(300) as pool:
        results = pool.map(get, list(range(1000)))

    assert labelbox.exceptions.ApiLimitError in {type(r) for r in results}

    # Sleep at the end of this test to allow other tests to execute.
    time.sleep(60)
