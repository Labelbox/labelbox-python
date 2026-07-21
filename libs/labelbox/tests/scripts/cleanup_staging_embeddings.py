import argparse
import os
from typing import Any, Callable, Iterable, List, Optional, Sequence
from urllib.parse import urlparse

from lbox.exceptions import LabelboxError

from labelbox import Client
from tests.embedding_cleanup import (
    LEGACY_NAME_RE,
    select_stale_embeddings,
)

STAGING_GRAPHQL_ENDPOINT = "https://api.lb-stage.xyz/graphql"
STAGING_REST_ENDPOINT = "https://api.lb-stage.xyz/api/v1"
STAGING_REST_HOST = "api.lb-stage.xyz"


def _parse_boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("expected 'true' or 'false'")


def assert_staging_rest_endpoint(client: Any) -> None:
    effective_host = urlparse(client.rest_endpoint).hostname
    if effective_host != STAGING_REST_HOST:
        raise RuntimeError(
            "Refusing to inspect embeddings: the effective REST endpoint "
            f"host is {effective_host!r}, expected {STAGING_REST_HOST!r}"
        )


def create_staging_client(
    *,
    api_key: Optional[str] = None,
    client_factory: Callable[..., Any] = Client,
) -> Any:
    effective_api_key = api_key or os.environ.get("LABELBOX_TEST_API_KEY")
    if not effective_api_key:
        raise RuntimeError("LABELBOX_TEST_API_KEY is required")

    client = client_factory(
        api_key=effective_api_key,
        endpoint=STAGING_GRAPHQL_ENDPOINT,
        rest_endpoint=STAGING_REST_ENDPOINT,
    )
    assert_staging_rest_endpoint(client)
    return client


def select_cleanup_candidates(
    embeddings: Iterable[Any], now: float
) -> List[Any]:
    embeddings = list(embeddings)
    stale_v2_ids = {
        embedding.id for embedding in select_stale_embeddings(embeddings, now)
    }
    return [
        embedding
        for embedding in embeddings
        if embedding.custom
        and (
            LEGACY_NAME_RE.fullmatch(embedding.name) is not None
            or embedding.id in stale_v2_ids
        )
    ]


def run_cleanup(client: Any, *, dry_run: bool, now: float) -> int:
    # Validate the effective endpoint immediately before the first API read.
    assert_staging_rest_endpoint(client)
    print(
        "WARNING: this cleanup cannot detect active owners. Confirm both "
        "Labelbox Python SDK Staging and LBox Develop are quiet, and run "
        "dry-run first."
    )
    candidates = select_cleanup_candidates(client.get_embeddings(), now)

    print(f"Embedding cleanup candidates ({len(candidates)}):")
    for embedding in candidates:
        print(f"candidate id={embedding.id} name={embedding.name}")

    if dry_run:
        print(
            "[embedding-cleanup] "
            f"run={os.getenv('GITHUB_RUN_ID', '-')} dry_run=1 "
            f"candidates={len(candidates)} deleted=0 failed=0"
        )
        return 0

    deleted = 0
    failed = []
    for embedding in candidates:
        try:
            embedding.delete()
            deleted += 1
            print(f"deleted id={embedding.id} name={embedding.name}")
        except LabelboxError as error:
            failed.append(embedding.id)
            print(
                f"failed id={embedding.id} name={embedding.name} error={error}"
            )

    print(
        "[embedding-cleanup] "
        f"run={os.getenv('GITHUB_RUN_ID', '-')} dry_run=0 "
        f"candidates={len(candidates)} deleted={deleted} "
        f"failed={len(failed)}"
    )
    return 1 if failed else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Clean leaked custom embeddings from the shared staging org. "
            "Confirm Labelbox Python SDK Staging and LBox Develop are quiet "
            "and run dry-run first."
        )
    )
    parser.add_argument(
        "--dry-run",
        type=_parse_boolean,
        default=True,
        help="true (default) lists only; false deletes every candidate",
    )
    args = parser.parse_args(argv)

    import time

    return run_cleanup(
        create_staging_client(),
        dry_run=args.dry_run,
        now=time.time(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
