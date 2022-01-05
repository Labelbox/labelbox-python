import os
import re

from azure.storage.blob import BlobServiceClient, ContainerClient
from loguru import logger
from urllib.parse import urlparse

def extract_file_path(path: str) -> str:
    """Extract the file path after from a blob storage URL.

    Container name (the first path segment) is excluded.

    >>> path = "https://storage-acct-name.blob.core.windows.net/container/imgs/1001.jpg"
    >>> extract_file_path(path)
    ... "imgs/1001.jpg"
    """
    return urlparse(path).path.split('/', maxsplit=2)[-1]


def create_blobstorage_client(azure_connection: str, azure_container_name: str) -> ContainerClient:
    service = BlobServiceClient.from_connection_string(azure_connection)
    return service.get_container_client(azure_container_name)


def get_connection_string() -> str:
    try:
        return os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    except KeyError:
        logger.exception("Environment variable AZURE_STORAGE_CONNECTION_STRING is not set")

