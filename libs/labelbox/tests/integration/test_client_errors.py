import os
import time
from multiprocessing.dummy import Pool

import lbox.exceptions
import pytest
from google.api_core.exceptions import RetryError

import labelbox.client
from labelbox.schema.media_type import MediaType

# Deployed API environments replace the message of every GraphQL validation
# error with this fixed string, so that schema details (field names, "Did you
# mean ..." hints) are not exposed to clients. The error code is unchanged.
# Only an API that does not hide schema details, such as one run locally,
# still returns the detailed message.
MASKED_VALIDATION_ERROR_MESSAGE = "GraphQL validation error"


def test_missing_api_key():
    key = os.environ.get(lbox.request_client._LABELBOX_API_KEY, None)
    if key is not None:
        del os.environ[lbox.request_client._LABELBOX_API_KEY]

    with pytest.raises(lbox.exceptions.AuthenticationError) as excinfo:
        labelbox.client.Client()

    assert excinfo.value.message == "Labelbox API key not provided"

    if key is not None:
        os.environ[lbox.request_client._LABELBOX_API_KEY] = key


def test_bad_key(rand_gen):
    bad_key = "BAD_KEY_" + rand_gen(str)
    client = labelbox.client.Client(api_key=bad_key)

    with pytest.raises(lbox.exceptions.AuthenticationError) as excinfo:
        client.create_project(name=rand_gen(str), media_type=MediaType.Image)


def test_syntax_error(client):
    with pytest.raises(lbox.exceptions.InvalidQueryError) as excinfo:
        client.execute("asda", check_naming=False)
    assert excinfo.value.message.startswith("Syntax Error:")


def test_semantic_error(client):
    with pytest.raises(lbox.exceptions.InvalidQueryError) as excinfo:
        client.execute("query {bbb {id}}", check_naming=False)
    message = excinfo.value.message
    assert message == MASKED_VALIDATION_ERROR_MESSAGE or message.startswith(
        'Cannot query field "bbb"'
    )


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
    # The complexity limit is a validation rule, so where validation messages
    # are masked its "Query complexity limit exceeded" message is replaced as
    # well. The client then has nothing left to tell it apart from any other
    # validation failure and raises InvalidQueryError; ValidationFailedError is
    # only reachable against an API that does not hide schema details.
    with pytest.raises(
        (
            lbox.exceptions.InvalidQueryError,
            lbox.exceptions.ValidationFailedError,
        )
    ) as excinfo:
        client.execute(
            "{projects {datasets {dataRows {labels {id}}}}}", check_naming=False
        )
    if isinstance(excinfo.value, lbox.exceptions.ValidationFailedError):
        assert excinfo.value.message == "Query complexity limit exceeded"
    else:
        assert excinfo.value.message == MASKED_VALIDATION_ERROR_MESSAGE


def test_resource_not_found_error(client):
    with pytest.raises(lbox.exceptions.ResourceNotFoundError):
        client.get_project("invalid project ID")


def test_network_error(client):
    client = labelbox.client.Client(
        api_key=client._request_client.api_key, endpoint="not_a_valid_URL"
    )

    with pytest.raises(lbox.exceptions.NetworkError) as excinfo:
        client.create_project(name="Project name", media_type=MediaType.Image)


@pytest.mark.skip("timeouts cause failure before rate limit")
def test_api_limit_error(client):
    def get(arg):
        try:
            return client.get_user()
        except lbox.exceptions.ApiLimitError as e:
            return e

    # Rate limited at 1500 + buffer
    n = 1600
    # max of 30 concurrency before the service becomes unavailable
    with Pool(30) as pool:
        start = time.time()
        results = list(pool.imap(get, range(n)), total=n)
        elapsed = time.time() - start

    assert elapsed < 60, "Didn't finish fast enough"
    assert lbox.exceptions.ApiLimitError in {type(r) for r in results}

    # Sleep at the end of this test to allow other tests to execute.
    time.sleep(60)
