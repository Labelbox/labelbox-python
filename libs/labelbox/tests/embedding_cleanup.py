import os
import re
import time
import uuid
from random import uniform
from typing import Any, Callable, Iterable, List, Optional

from lbox.exceptions import LabelboxError, MalformedQueryException

EMBEDDING_NAME_PREFIX_V2 = "sdk-int-ci-v2-"
EMBEDDING_CAP_ERROR_SNIPPET = "Max limit of custom embeddings"
# Creating and deleting an embedding are GraphQL mutations, and the API
# reports the cap with the MALFORMED_REQUEST code. The SDK raises that as
# MalformedQueryException, which does not derive from LabelboxError, so
# catching LabelboxError alone lets the cap error through unhealed.
EMBEDDING_CAP_ERROR_TYPES = (LabelboxError, MalformedQueryException)
EMBEDDING_STALE_TTL_SECONDS = 12 * 3600
LEGACY_NAME_RE = re.compile(r"^sdk-int-[0-9a-f]{32}$")

_V2_NAME_RE = re.compile(
    rf"^{re.escape(EMBEDDING_NAME_PREFIX_V2)}(\d+)-[0-9a-f]{{10}}$"
)
_MAX_CREATE_ATTEMPTS = 3


def build_embedding_name(now: float) -> str:
    return f"{EMBEDDING_NAME_PREFIX_V2}{int(now)}-{uuid.uuid4().hex[:10]}"


def parse_embedding_created_at(name: str) -> Optional[int]:
    match = _V2_NAME_RE.fullmatch(name)
    return int(match.group(1)) if match is not None else None


def select_stale_embeddings(embeddings: Iterable[Any], now: float) -> List[Any]:
    stale_embeddings = []
    for embedding in embeddings:
        created_at = parse_embedding_created_at(embedding.name)
        if (
            embedding.custom
            and created_at is not None
            and now - created_at > EMBEDDING_STALE_TTL_SECONDS
        ):
            stale_embeddings.append(embedding)
    return stale_embeddings


def is_embedding_cap_error(error: Exception) -> bool:
    return EMBEDDING_CAP_ERROR_SNIPPET in str(error)


def create_embedding_with_heal(
    *,
    create_embedding: Callable[[], Any],
    list_embeddings: Callable[[], Iterable[Any]],
    delete_embedding: Callable[[Any], None],
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.time,
    retry_delay: Callable[[float, float], float] = uniform,
    print_fn: Callable[[str], None] = print,
) -> Any:
    last_swept_count = None

    for attempt in range(1, _MAX_CREATE_ATTEMPTS + 1):
        try:
            return create_embedding()
        except EMBEDDING_CAP_ERROR_TYPES as error:
            if not is_embedding_cap_error(error):
                raise

            if attempt == _MAX_CREATE_ATTEMPTS:
                if last_swept_count == 0:
                    print_fn(
                        "[embedding-fixture-heal] no stale embeddings were "
                        "swept; the cap appears held by live fixtures and/or "
                        "legacy/foreign names that automated healing "
                        "deliberately does not touch"
                    )
                raise

            stale_embeddings = select_stale_embeddings(list_embeddings(), now())
            for embedding in stale_embeddings:
                try:
                    delete_embedding(embedding)
                except EMBEDDING_CAP_ERROR_TYPES:
                    # Another worker may have deleted the same stale embedding.
                    # Several jobs hit the cap at once and sweep the same
                    # names, and the delete is a GraphQL mutation too, so it
                    # can fail with either kind of error.
                    pass

            last_swept_count = len(stale_embeddings)
            sample = ",".join(
                embedding.id for embedding in stale_embeddings[:3]
            )
            print_fn(
                "[embedding-fixture-heal] "
                f"run={os.getenv('GITHUB_RUN_ID', '-')} "
                f"worker={os.getenv('PYTEST_XDIST_WORKER', '-')} "
                f"attempt={attempt} cap_hit=1 "
                f"swept={last_swept_count} sample={sample or '-'}"
            )
            sleep(retry_delay(2, 8))

    raise AssertionError("unreachable")
