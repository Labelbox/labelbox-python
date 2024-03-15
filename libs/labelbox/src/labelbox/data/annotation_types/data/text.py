from typing import Callable, Optional

import requests
from requests.exceptions import ConnectTimeout
from google.api_core import retry

from labelbox import pydantic_compat
from labelbox.exceptions import InternalServerError
from labelbox.typing_imports import Literal
from labelbox.utils import _NoCoercionMixin
from .base_data import BaseData


class TextData(BaseData, _NoCoercionMixin):
    """
    Represents text data. Requires arg file_path, text, or url

    >>> TextData(text="")

    Args:
        file_path (str)
        text (str)
        url (str)
    """
    class_name: Literal["TextData"] = "TextData"
    file_path: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None

    @property
    def value(self) -> str:
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
            text = self.fetch_remote()
            self.text = text
            return text
        else:
            raise ValueError("Must set either url, file_path or im_bytes")

    def set_fetch_fn(self, fn):
        object.__setattr__(self, 'fetch_remote', lambda: fn(self))

    @retry.Retry(deadline=15.,
                 predicate=retry.if_exception_type(ConnectTimeout,
                                                   InternalServerError))
    def fetch_remote(self) -> str:
        """
        Method for accessing url.

        If url is not publicly accessible or requires another access pattern
        simply override this function
        """
        response = requests.get(self.url)
        if response.status_code in [500, 502, 503, 504]:
            raise labelbox.exceptions.InternalServerError(response.text)
        response.raise_for_status()
        return response.text

    @retry.Retry(deadline=15.)
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

    @pydantic_compat.root_validator
    def validate_date(cls, values):
        file_path = values.get("file_path")
        text = values.get("text")
        url = values.get("url")
        uid = values.get('uid')
        global_key = values.get('global_key')
        if uid == file_path == text == url == global_key == None:
            raise ValueError(
                "One of `file_path`, `text`, `uid`, `global_key` or `url` required."
            )
        return values

    def __repr__(self) -> str:
        return  f"TextData(file_path={self.file_path}," \
                f"text={self.text[:30] + '...' if self.text is not None else None}," \
                f"url={self.url})"

    class config:
        # Required for discriminating between data types
        extra = 'forbid'
