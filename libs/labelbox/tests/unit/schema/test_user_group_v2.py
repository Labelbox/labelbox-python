from unittest.mock import MagicMock

import pytest

from labelbox.schema.user_group_v2 import Member, UserGroupV2


@pytest.fixture
def client():
    return MagicMock()


def test_parse_members_csv_empty(client):
    group = UserGroupV2(client)
    assert group._parse_members_csv("") == []
    assert group._parse_members_csv("\n") == []


def test_parse_members_csv_header_only(client):
    group = UserGroupV2(client)
    assert group._parse_members_csv("email\n") == []


def test_parse_members_csv_single_member(client):
    group = UserGroupV2(client)
    result = group._parse_members_csv("email\ntest@example.com")
    assert len(result) == 1
    assert isinstance(result[0], Member)
    assert result[0].email == "test@example.com"


def test_parse_members_csv_multiple_members(client):
    group = UserGroupV2(client)
    csv_data = "email\ntest1@example.com\ntest2@example.com\ntest3@example.com"
    result = group._parse_members_csv(csv_data)
    assert len(result) == 3
    assert [m.email for m in result] == [
        "test1@example.com",
        "test2@example.com",
        "test3@example.com",
    ]


def test_parse_members_csv_handles_whitespace(client):
    group = UserGroupV2(client)
    csv_data = "email\n  test@example.com  \n\nother@example.com\n"
    result = group._parse_members_csv(csv_data)
    assert len(result) == 2
    assert result[0].email == "test@example.com"
    assert result[1].email == "other@example.com"
