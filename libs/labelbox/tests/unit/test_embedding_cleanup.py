from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import pytest
from lbox.exceptions import LabelboxError

from tests.embedding_cleanup import (
    EMBEDDING_CAP_ERROR_SNIPPET,
    EMBEDDING_NAME_PREFIX_V2,
    EMBEDDING_STALE_TTL_SECONDS,
    build_embedding_name,
    create_embedding_with_heal,
    is_embedding_cap_error,
    parse_embedding_created_at,
    select_stale_embeddings,
)
from tests.scripts.cleanup_staging_embeddings import (
    STAGING_GRAPHQL_ENDPOINT,
    STAGING_REST_ENDPOINT,
    _parse_boolean,
    create_staging_client,
    run_cleanup,
)


def _embedding(
    embedding_id: str,
    name: str,
    *,
    custom: bool = True,
    delete: Mock = None,
):
    return SimpleNamespace(
        id=embedding_id,
        name=name,
        custom=custom,
        delete=delete or Mock(),
    )


def _v2_name(created_at: int, suffix: str = "0123456789") -> str:
    return f"{EMBEDDING_NAME_PREFIX_V2}{created_at}-{suffix}"


def _cap_error() -> LabelboxError:
    return LabelboxError(f"{EMBEDDING_CAP_ERROR_SNIPPET}: 10")


def test_build_and_parse_embedding_name_round_trip():
    with patch(
        "tests.embedding_cleanup.uuid.uuid4",
        return_value=SimpleNamespace(hex="abcdef0123456789abcdef0123456789"),
    ):
        name = build_embedding_name(1_725_000_000.75)

    assert name == "sdk-int-ci-v2-1725000000-abcdef0123"
    assert parse_embedding_created_at(name) == 1_725_000_000


@pytest.mark.parametrize(
    "name",
    [
        "sdk-int-abcdef0123456789abcdef0123456789",
        "sdk-int-ci-v2-1725000000-abcdef012",
        "sdk-int-ci-v2-1725000000-abcdef01234",
        "sdk-int-ci-v2-1725000000-abcdefghi0",
        "foreign-ci-v2-1725000000-abcdef0123",
        "sdk-int-ci-v2--1725000000-abcdef0123",
    ],
)
def test_parse_embedding_created_at_rejects_non_v2_names(name):
    assert parse_embedding_created_at(name) is None


def test_select_stale_embeddings_keeps_only_expired_custom_v2_names():
    now = 1_725_000_000
    stale = _embedding(
        "stale",
        _v2_name(now - EMBEDDING_STALE_TTL_SECONDS - 1),
    )
    fresh = _embedding("fresh", _v2_name(now - 60))
    boundary = _embedding(
        "boundary", _v2_name(now - EMBEDDING_STALE_TTL_SECONDS)
    )
    legacy = _embedding("legacy", "sdk-int-abcdef0123456789abcdef0123456789")
    non_custom = _embedding(
        "non-custom",
        _v2_name(now - EMBEDDING_STALE_TTL_SECONDS - 1),
        custom=False,
    )

    assert select_stale_embeddings(
        [fresh, stale, boundary, legacy, non_custom], now
    ) == [stale]


def test_embedding_cap_error_matcher_is_fail_closed():
    assert is_embedding_cap_error(_cap_error())
    assert not is_embedding_cap_error(LabelboxError("permission denied"))


def test_workflow_boolean_input_is_parsed_defensively():
    assert _parse_boolean("true") is True
    assert _parse_boolean("false") is False


def test_heal_retries_twice_then_creates_and_deletes_only_stale_v2():
    now_value = 1_725_000_000
    stale = _embedding(
        "stale",
        _v2_name(now_value - EMBEDDING_STALE_TTL_SECONDS - 1),
    )
    fresh = _embedding("fresh", _v2_name(now_value - 1))
    legacy = _embedding("legacy", "sdk-int-abcdef0123456789abcdef0123456789")
    non_custom = _embedding(
        "non-custom",
        _v2_name(now_value - EMBEDDING_STALE_TTL_SECONDS - 1),
        custom=False,
    )
    created = object()
    create = Mock(side_effect=[_cap_error(), _cap_error(), created])
    list_embeddings = Mock(side_effect=[[stale, fresh, legacy, non_custom], []])
    delete = Mock()
    sleep = Mock()

    result = create_embedding_with_heal(
        create_embedding=create,
        list_embeddings=list_embeddings,
        delete_embedding=delete,
        sleep=sleep,
        now=Mock(return_value=now_value),
        retry_delay=Mock(return_value=4),
        print_fn=Mock(),
    )

    assert result is created
    assert create.call_count == 3
    assert list_embeddings.call_count == 2
    assert delete.call_args_list == [call(stale)]
    assert sleep.call_args_list == [call(4), call(4)]


def test_heal_third_cap_error_is_terminal_without_another_sweep_or_sleep():
    final_error = _cap_error()
    create = Mock(side_effect=[_cap_error(), _cap_error(), final_error])
    list_embeddings = Mock(return_value=[])
    delete = Mock()
    sleep = Mock()
    print_fn = Mock()

    with pytest.raises(LabelboxError) as raised:
        create_embedding_with_heal(
            create_embedding=create,
            list_embeddings=list_embeddings,
            delete_embedding=delete,
            sleep=sleep,
            now=Mock(return_value=1_725_000_000),
            retry_delay=Mock(return_value=4),
            print_fn=print_fn,
        )

    assert raised.value is final_error
    assert create.call_count == 3
    assert list_embeddings.call_count == 2
    delete.assert_not_called()
    assert sleep.call_count == 2
    assert any(
        "live fixtures and/or legacy/foreign names" in args[0]
        for args, _ in print_fn.call_args_list
    )


def test_heal_non_cap_error_is_reraised_without_side_effects():
    non_cap_error = LabelboxError("permission denied")
    create = Mock(side_effect=non_cap_error)
    list_embeddings = Mock()
    delete = Mock()
    sleep = Mock()

    with pytest.raises(LabelboxError) as raised:
        create_embedding_with_heal(
            create_embedding=create,
            list_embeddings=list_embeddings,
            delete_embedding=delete,
            sleep=sleep,
        )

    assert raised.value is non_cap_error
    create.assert_called_once_with()
    list_embeddings.assert_not_called()
    delete.assert_not_called()
    sleep.assert_not_called()


def test_bootstrap_client_uses_staging_endpoints_and_checks_effective_host():
    staging_client = SimpleNamespace(rest_endpoint=STAGING_REST_ENDPOINT)
    client_factory = Mock(return_value=staging_client)

    assert (
        create_staging_client(
            api_key="staging-key", client_factory=client_factory
        )
        is staging_client
    )
    client_factory.assert_called_once_with(
        api_key="staging-key",
        endpoint=STAGING_GRAPHQL_ENDPOINT,
        rest_endpoint=STAGING_REST_ENDPOINT,
    )

    client_factory.return_value = SimpleNamespace(
        rest_endpoint="https://api.labelbox.com/api/v1"
    )
    with pytest.raises(RuntimeError, match="effective REST endpoint"):
        create_staging_client(
            api_key="staging-key", client_factory=client_factory
        )


def test_bootstrap_host_check_fails_before_listing():
    client = SimpleNamespace(
        rest_endpoint="https://api.labelbox.com/api/v1",
        get_embeddings=Mock(),
    )

    with pytest.raises(RuntimeError, match="effective REST endpoint"):
        run_cleanup(client, dry_run=True, now=1_725_000_000)

    client.get_embeddings.assert_not_called()


def test_cleanup_dry_run_lists_without_deleting(capsys):
    legacy = _embedding("legacy", "sdk-int-abcdef0123456789abcdef0123456789")
    client = SimpleNamespace(
        rest_endpoint=STAGING_REST_ENDPOINT,
        get_embeddings=Mock(return_value=[legacy]),
    )

    assert run_cleanup(client, dry_run=True, now=1_725_000_000) == 0
    legacy.delete.assert_not_called()
    assert "candidate id=legacy" in capsys.readouterr().out


def test_cleanup_real_run_attempts_every_candidate_and_reports_failures():
    failed_delete = Mock(side_effect=LabelboxError("delete failed"))
    first = _embedding(
        "first",
        "sdk-int-abcdef0123456789abcdef0123456789",
        delete=failed_delete,
    )
    second = _embedding("second", "sdk-int-0123456789abcdef0123456789abcdef")
    client = SimpleNamespace(
        rest_endpoint=STAGING_REST_ENDPOINT,
        get_embeddings=Mock(return_value=[first, second]),
    )

    assert run_cleanup(client, dry_run=False, now=1_725_000_000) == 1
    first.delete.assert_called_once_with()
    second.delete.assert_called_once_with()
