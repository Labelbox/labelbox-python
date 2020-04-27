'''Unit test utilities for mocking network calls.'''
import contextlib
from datetime import datetime
import json
from typing import Any, Dict, Generator

from labelbox import Client, Project
import pytest
from snapshottest.module import SnapshotTest
from unittest import mock


class MockResponse:
    '''Mocked response to return for any network call.'''

    def __init__(self,
                 json_data: Dict[str, Any],
                 status_code: int) -> None:
        '''Initializes with response package and code.

        Args:
            json_data: a dict mocking the json response.
            status_code: a status code mocking response code.
        '''
        self.json_data = json_data
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        '''Returns json package as a dict.'''
        return self.json_data

    def text(self) -> str:
        '''Returns text dump of the response package.'''
        return json.dump(self.json())


@contextlib.contextmanager
def mock_client(
        snapshot: SnapshotTest,
        mock_response: MockResponse) -> Generator:
    '''Mocks a Client to compare any request.post calls against a snapshot.

    Args:
        snapshot: snapshot object for comparison
        mock_response: mocked response object from the intercepted network
            call.
    Yields:
        Client object
    '''
    with mock.patch('requests.post') as mock_request:
        mock_request.return_value = mock_response
        yield Client(api_key='dummy_key')
        reqs = []
        for args, kwargs in mock_request.call_args_list:
            reqs.append((args, kwargs))
        snapshot.assert_match(reqs)


@contextlib.contextmanager
def mock_project(snapshot: SnapshotTest, mock_response: MockResponse) -> Project:
    '''Mocks a Project using a mocked Client.

    Mocked Client takes a snapshot and mock response for any network calls.

    Args:
        See Args for mock_client.
    Yields:
        a Project object with mocked out field values.
    '''
    now_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    field_values = {
        'id': 'mock_id',
        'deleted': False,
        'name': 'mock_project',
        'description': 'mock project',
        'updatedAt': now_time,
        'createdAt': now_time,
        'setupComplete': now_time,
        'lastActivityTime': now_time,
        'autoAuditNumberOfLabels': 0,
        'autoAuditPercentage': 0,
    }

    with mock_client(snapshot, mock_response) as client:
        yield Project(client, field_values)
