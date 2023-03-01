import os

from azure.storage.blob import BlobServiceClient, ContainerClient
from loguru import logger
from typing import Dict
from urllib.parse import urlparse


def extract_file_path(path: str) -> str:
    """Extract the file path after from a blob storage URL.

    Container name (the first path segment) is excluded.

    >>> path = "https://storage-acct-name.blob.core.windows.net/container/imgs/1001.jpg"
    >>> extract_file_path(path)
    ... "imgs/1001.jpg"
    """
    return urlparse(path).path.split('/', maxsplit=2)[-1]


def create_blob_service_client(azure_connection: str, azure_container_name: str) -> ContainerClient:
    service = BlobServiceClient.from_connection_string(azure_connection)
    return service.get_container_client(azure_container_name)


def get_connection_string() -> str:
    try:
        return os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    except KeyError:
        logger.exception("Environment variable AZURE_STORAGE_CONNECTION_STRING is not set")


def get_blob_metadata(blob_service_client, azure_blob_name):
    blob_client = blob_service_client.get_blob_client(blob=azure_blob_name)
    return blob_client.get_blob_properties().metadata


def set_blob_metadata(
    blob_service_client, azure_blob_name: str, metadata: Dict
):
    blob_client = blob_service_client.get_blob_client(blob=azure_blob_name)
    blob_client.set_blob_metadata(metadata)

