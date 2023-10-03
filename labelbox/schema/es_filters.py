SEARCH_LIMIT = 2_000
ISO_8061_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def build_id_filters(ids: list,
                     type_name: str,
                     search_where_limit: int = SEARCH_LIMIT) -> dict:
    if not isinstance(ids, list):
        raise ValueError(f"{type_name} filter expects a list.")
    if len(ids) == 0:
        raise ValueError(f"{type_name} filter expects a non-empty list.")
    if len(ids) > search_where_limit:
        raise ValueError(
            f"{type_name} filter only supports a max of {search_where_limit} items."
        )
    return {"ids": ids, "operator": "is", "type": type_name}
