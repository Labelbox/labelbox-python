import io
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from urllib.parse import urlparse
from labelbox.exceptions import LabelboxError

import requests
from requests import Session, Response

logger = logging.getLogger(__name__)


class AdvClient:

    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.session = self._create_session()

    def create_embedding(self, name: str, dims: int) -> Dict[str, Any]:
        data = {"name": name, "dims": dims}
        return self._request("POST", "/adv/v1/embeddings", data)

    def delete_embedding(self, id: str):
        return self._request("DELETE", f"/adv/v1/embeddings/{id}")

    def get_embedding(self, id: str) -> Dict[str, Any]:
        return self._request("GET", f"/adv/v1/embeddings/{id}")

    def get_embeddings(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/adv/v1/embeddings").get("results", [])

    def import_vectors_from_file(self, id: str, file_path: str, callback=None):
        self._send_ndjson(f"/adv/v1/embeddings/{id}/_import_ndjson", file_path,
                          callback)

    def get_imported_vector_count(self, id: str) -> int:
        data = self._request("GET", f"/adv/v1/embeddings/{id}/vectors/_count")
        return data.get("count", 0)

    def _create_session(self) -> Session:
        session = requests.session()
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        return session

    def _request(self,
                 method: str,
                 path: str,
                 data: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        requests_data = None
        if data:
            requests_data = json.dumps(data)
        response = self.session.request(method,
                                        url,
                                        data=requests_data,
                                        headers=headers)
        if response.status_code != requests.codes.ok:
            message = response.json().get('message')
            if message:
                raise LabelboxError(message)
            else:
                response.raise_for_status()
        return response.json()

    def _send_ndjson(self,
                     path: str,
                     file_path: str,
                     callback: Optional[Callable[[Dict[str, Any]],
                                                 None]] = None):
        """
        Sends an NDJson file in chunks.

        Args:
            path: The URL path
            file_path: The path to the NDJSON file.
            callback: A callback to run for each chunk uploaded.
        """

        def upload_chunk(_buffer, _count):
            _buffer.write(b"\n")
            _headers = {
                "Content-Type": "application/x-ndjson",
                "X-Content-Lines": str(_count),
                "Content-Length": str(buffer.tell())
            }
            rsp = self._send_bytes(f"{self.endpoint}{path}", _buffer, _headers)
            rsp.raise_for_status()
            if callback:
                callback(rsp.json())

        buffer = io.BytesIO()
        count = 0
        with open(file_path, 'rb') as fp:
            for line in fp:
                buffer.write(line)
                count += 1
                if count >= 1000:
                    upload_chunk(buffer, count)
                    buffer = io.BytesIO()
                    count = 0
        if count:
            upload_chunk(buffer, count)

    def _send_bytes(self,
                    url: str,
                    buffer: io.BytesIO,
                    headers: Optional[Dict[str, Any]] = None) -> Response:
        buffer.seek(0)
        return self.session.put(url, headers=headers, data=buffer)

    @classmethod
    def factory(cls, api_endpoint: str, api_key: str) -> "AdvClient":
        parsed_url = urlparse(api_endpoint)
        endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/adv"
        return AdvClient(endpoint, api_key)
