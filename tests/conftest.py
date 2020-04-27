import contextlib
from datetime import datetime
import json
from typing import Any, Dict, Generator

from labelbox import Client, Project
import pytest
from snapshottest.module import SnapshotTest
from unittest import mock


class MockResponse:
    def __init__(self,
                 json_data: Dict[str, Any],
                 status_code: int) -> None:
        self.json_data = json_data
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        return self.json_data

    def text(self) -> str:
        return json.dump(self.json())


@contextlib.contextmanager
def mock_client(
        snapshot: SnapshotTest,
        mock_response: MockResponse) -> Generator:
    with mock.patch('requests.post') as mock_request:
        mock_request.return_value = mock_response
        yield Client(api_key='dummy_key')
        reqs = []
        for args, kwargs in mock_request.call_args_list:
            reqs.append((args, kwargs))
        snapshot.assert_match(reqs)


@contextlib.contextmanager
def mock_project(snapshot: SnapshotTest, mock_response: MockResponse) -> Project:
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
