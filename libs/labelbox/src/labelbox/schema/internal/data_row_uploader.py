from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import List

from labelbox import pydantic_compat
from labelbox.schema.internal.data_row_upsert_item import DataRowUpsertItem
from labelbox.schema.internal.descriptor_file_creator import DescriptorFileCreator


class UploadManifest(pydantic_compat.BaseModel):
    source: str
    item_count: int
    chunk_uris: List[str]


SOURCE_SDK = "SDK"


def upload_in_chunks(client, specs: List[DataRowUpsertItem],
                     file_upload_thread_count: int,
                     max_chunk_size_bytes: int) -> UploadManifest:
    empty_specs = list(filter(lambda spec: spec.is_empty(), specs))

    if empty_specs:
        ids = list(map(lambda spec: spec.id.get("value"), empty_specs))
        raise ValueError(f"The following items have an empty payload: {ids}")

    chunk_uris = DescriptorFileCreator(client).create(
        specs, max_chunk_size_bytes=max_chunk_size_bytes)

    return UploadManifest(source=SOURCE_SDK,
                          item_count=len(specs),
                          chunk_uris=chunk_uris)
