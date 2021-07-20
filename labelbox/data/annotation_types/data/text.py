from typing import Callable, Optional

import requests
from pydantic import root_validator

from .base_data import BaseData


class TextData(BaseData):
    """
    Represents text data
    """
    file_path: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None

    @property
    def data(self) -> str:
        """
        Property that unifies the data access pattern for all references to the text.

        Returns:
            string representation of the text
        """
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
        """
        Utility for creating a url from any of the other text references.

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            url for the text
        """
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
        text = values.get("text")
        url = values.get("url")
        uid = values.get('uid')
        if uid == file_path == text == url == None:
            raise ValueError(
                "One of `file_path`, `text`, `uid`, or `url` required.")
        return values

    class config:
        extra = 'forbid'
