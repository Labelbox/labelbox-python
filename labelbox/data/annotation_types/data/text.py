from typing import Callable, Optional

import requests
from pydantic import ValidationError, root_validator

from labelbox.data.annotation_types.reference import DataRowRef


class TextData(DataRowRef):
    file_path: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None

    @property
    def data(self) -> str:
        if self.text:
            return self.text
        elif self.file_path:
            with open(self.file_path, "r") as file:
                text = file.read()
            self.text = text
            return text
        elif self.url:
            response = requests.get(self.url)
            response.raise_for_status()
            text = response.text
            self.text = text
            return text
        else:
            raise ValueError("Must set either url, file_path or im_bytes")

    def create_url(self, signer: Callable[[bytes], str]) -> None:
        if self.url is not None:
            return self.url
        elif self.file_path is not None:
            with open(self.file_path, 'rb') as file:
                self.url = signer(file.read())
        elif self.text is not None:
            self.url = signer(self.text.encode())
        else:
            raise ValueError(
                "One of url, im_bytes, file_path, numpy must not be None.")
        return self.url

    @root_validator
    def validate_date(cls, values):
        file_path = values.get("file_path")
        im_bytes = values.get("text")
        url = values.get("url")
        if file_path == im_bytes == url == None:
            raise ValidationError(
                "One of `file_path`, `im_bytes`, or `url` required.")
        return values

    class config:
        extra = 'forbid'
