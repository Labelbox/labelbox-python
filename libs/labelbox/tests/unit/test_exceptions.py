import pytest

from labelbox.exceptions import error_message_for_unparsed_graphql_error


@pytest.mark.parametrize('exception_message, expected_result', [
    ("Unparsed errors on query execution: [{'message': 'Cannot create model config for project because model setup is complete'}]",
     "Cannot create model config for project because model setup is complete"),
    ("blah blah blah", "Unknown error"),
])
def test_client_unparsed_exception_messages(exception_message, expected_result):
    assert error_message_for_unparsed_graphql_error(
        exception_message) == expected_result
