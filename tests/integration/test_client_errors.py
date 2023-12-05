from multiprocessing.dummy import Pool
import os
import time
import pytest
from google.api_core.exceptions import RetryError

from labelbox import Project, Dataset, User
import labelbox.client
import labelbox.exceptions


def test_missing_api_key():
    key = os.environ.get(labelbox.client._LABELBOX_API_KEY, None)
    if key is not None:
        del os.environ[labelbox.client._LABELBOX_API_KEY]

    with pytest.raises(labelbox.exceptions.AuthenticationError) as excinfo:
        labelbox.client.Client()

    assert excinfo.value.message == "Labelbox API key not provided"

    if key is not None:
        os.environ[labelbox.client._LABELBOX_API_KEY] = key


def test_bad_key(rand_gen):
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


def test_timeout_error(client, project):
    with pytest.raises(RetryError) as excinfo:
        query_str = """query getOntology {
        project (where: {id: %s}) {
            ontology {
                normalized
                }
            }
        } """ % (project.uid)

        # Setting connect timeout to 30s, and read timeout to 0.01s
        client.execute(query_str, check_naming=False, timeout=(30.0, 0.01))


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


def test_invalid_attribute_error(
    client,
    rand_gen,
):
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

    # Top-level-fetch
    with pytest.raises(labelbox.exceptions.InvalidAttributeError) as excinfo:
        client.get_projects(where=User.email == "email")
    assert excinfo.value.db_object_type == Project
    assert excinfo.value.field == {User.email}


@pytest.mark.skip("timeouts cause failure before rate limit")
def test_api_limit_error(client):

    def get(arg):
        try:
            return client.get_user()
        except labelbox.exceptions.ApiLimitError as e:
            return e

    # Rate limited at 1500 + buffer
    n = 1600
    # max of 30 concurrency before the service becomes unavailable
    with Pool(30) as pool:
        start = time.time()
        results = list(pool.imap(get, range(n)), total=n)
        elapsed = time.time() - start

    assert elapsed < 60, "Didn't finish fast enough"
    assert labelbox.exceptions.ApiLimitError in {type(r) for r in results}

    # Sleep at the end of this test to allow other tests to execute.
    time.sleep(60)
