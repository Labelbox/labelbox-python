import json
import logging

from typing import Any, List, Dict, Union

import requests

import labelbox.exceptions

logger = logging.getLogger(__name__)

ADV_EMDBEDDING_PATH = "/adv/v1/embeddings"


class DataRowEmbedding:
    """ Embedding info on a data row, which can be used against search use cases.

    >>> mdo = client.get_data_row_embedding()

    """

    def __init__(self, client):

        self._client = client

    def create_custom_embedding(self, name: str,
                                dims: str) -> Dict[str, Union[str, List[Any]]]:
        adv_embedding_endpoint_url = f"{self._client.adv_rest_endpoint}{ADV_EMDBEDDING_PATH}"
        data = json.dumps({"name": name, "dims": dims})

        response = requests.post(url=adv_embedding_endpoint_url,
                                 headers=self._client.headers,
                                 data=data)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            raise labelbox.exceptions.LabelboxError(
                "Failed to create custom embedding, message: ", response.text)

    def get_all_custom_embeddings(
            self) -> List[Dict[str, Union[str, List[Any]]]]:
        adv_embedding_endpoint_url = f"{self._client.adv_rest_endpoint}{ADV_EMDBEDDING_PATH}"
        response = requests.get(url=adv_embedding_endpoint_url,
                                headers=self._client.headers)

        if response.status_code == requests.codes.ok:
            return response.json()['results']
        else:
            raise labelbox.exceptions.LabelboxError(
                "Failed to get custom embedding, message: ", response.text)

    def delete_custom_embedding(self, embedding_id: str) -> None:
        adv_embedding_endpoint_url = f"{self._client.adv_rest_endpoint}{ADV_EMDBEDDING_PATH}/{embedding_id}"
        response = requests.delete(url=adv_embedding_endpoint_url,
                                   headers=self._client.headers)

        if response.status_code != requests.codes.ok:
            raise labelbox.exceptions.LabelboxError(
                "Failed to delete custom embedding, message: ", response.text)
