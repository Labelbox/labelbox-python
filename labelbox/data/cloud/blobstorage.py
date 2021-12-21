import os

from azure.storage.blob import BlobServiceClient, ContainerClient
from loguru import logger


def create_blobstorage_client(azure_connection: str, azure_container_name: str) -> ContainerClient:
    service = BlobServiceClient.from_connection_string(azure_connection)
    return service.get_container_client(azure_container_name)


def get_connection_string() -> str:
    try:
        return os.environ["AZURE_CONNECTION_STRING"]
    except KeyError as ex:
        logger.exception("Environment variable AZURE_CONNECTION_STRING is not set")

