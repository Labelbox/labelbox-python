from unittest.mock import MagicMock, Mock

from labelbox_dev.pagination import IdentifierPaginator, CursorPaginator, CURSOR_KEY, LIMIT_KEY
from labelbox_dev.entity import Entity


def cursor_pagination_get_request_mock(resource, params):
    ids = [str(idx) for idx in range(1, 10)]
    records = [{"id": idx} for idx in ids]
    cursor = params.get(CURSOR_KEY)
    limit = params.get(LIMIT_KEY)
    idx = ids.index(cursor) + 1 if cursor else 0
    data = records[idx:idx + limit]
    return {"data": data, "next": data[-1]['id'] if data else None}


def test_identifier_paginator():
    ids = [str(id_) for id_ in range(0, 1000, 200)]
    paginator = IdentifierPaginator('resource',
                                    Entity,
                                    ids, {'param1': 'val1'},
                                    limit=2)
    paginator._session = MagicMock()
    return_value = [{'id': ids[0]}, {'id': ids[1]}]
    paginator._session.get_request = MagicMock(return_value=return_value)
    items = list(paginator)
    assert len(items) == 6
    assert isinstance(items[0], Entity)
    assert paginator._session.get_request.call_count == 3


def test_curor_paginator():
    paginator = CursorPaginator('test', Entity, limit=2)
    paginator._session.get_request = Mock(
        side_effect=cursor_pagination_get_request_mock)
    entities = list(paginator)
    ids = [entity.id for entity in entities]
    paginator._session.get_request.call_count == 6
    assert ids == [str(idx) for idx in range(1, 10)]
