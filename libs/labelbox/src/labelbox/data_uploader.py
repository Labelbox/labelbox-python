import json
import logging
import mimetypes
import os
from typing import Optional

import requests
import requests.exceptions
from google.api_core import retry

from . import exceptions
from .request_client import RequestClient

logger = logging.getLogger(__name__)


class DataUploader:
    """A class to upload data.

    Contains info necessary for connecting to a Labelbox server (URL,
    authentication key).
    """

    def __init__(
        self,
        client: RequestClient,
    ) -> None:
        self._client = client

    @property
    def connection(self) -> requests.Session:
        return self._client._connection

    @retry.Retry(
        predicate=retry.if_exception_type(exceptions.InternalServerError)
    )
    def upload_data(
        self,
        content: bytes,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        sign: bool = False,
    ) -> str:
        """Uploads the given data (bytes) to Labelbox.

        Args:
            content: bytestring to upload
            filename: name of the upload
            content_type: content type of data uploaded
            sign: whether or not to sign the url

        Returns:
            str, the URL of uploaded data.

        Raises:
            exceptions.LabelboxError: If upload failed.
        """

        request_data = {
            "operations": json.dumps(
                {
                    "variables": {
                        "file": None,
                        "contentLength": len(content),
                        "sign": sign,
                    },
                    "query": """mutation UploadFile($file: Upload!, $contentLength: Int!,
                                            $sign: Boolean) {
                            uploadFile(file: $file, contentLength: $contentLength,
                                       sign: $sign) {url filename} } """,
                }
            ),
            "map": (None, json.dumps({"1": ["variables.file"]})),
        }

        files = {
            "1": (filename, content, content_type)
            if (filename and content_type)
            else content
        }
        headers = self.connection.headers.copy()
        headers.pop("Content-Type", None)
        request = requests.Request(
            "POST",
            self._client.endpoint,
            headers=headers,
            data=request_data,
            files=files,
        )

        prepped: requests.PreparedRequest = request.prepare()

        response = self.connection.send(prepped)

        if response.status_code == 502:
            error_502 = "502 Bad Gateway"
            raise exceptions.InternalServerError(error_502)
        elif response.status_code == 503:
            raise exceptions.InternalServerError(response.text)
        elif response.status_code == 520:
            raise exceptions.InternalServerError(response.text)

        try:
            file_data = response.json().get("data", None)
        except ValueError as e:  # response is not valid JSON
            raise exceptions.LabelboxError("Failed to upload, unknown cause", e)

        if not file_data or not file_data.get("uploadFile", None):
            try:
                errors = response.json().get("errors", [])
                error_msg = next(iter(errors), {}).get(
                    "message", "Unknown error"
                )
            except Exception:
                error_msg = "Unknown error"
            raise exceptions.LabelboxError(
                "Failed to upload, message: %s" % error_msg
            )

        return file_data["uploadFile"]["url"]

    def upload_file(self, path: str) -> str:
        """Uploads given path to local file.

        Also includes best guess at the content type of the file.

        Args:
            path (str): path to local file to be uploaded.
        Returns:
            str, the URL of uploaded data.
        Raises:
            labelbox.exceptions.LabelboxError: If upload failed.
        """
        content_type, _ = mimetypes.guess_type(path)
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            return self.upload_data(
                content=f.read(), filename=filename, content_type=content_type
            )
