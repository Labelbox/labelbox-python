import logging
import os
from posixpath import join as join_uri

import requests
import requests.exceptions

from labelbox import utils
from labelbox_dev import __version__ as SDK_VERSION
from labelbox_dev.exceptions import (AuthenticationError, LabelboxError,
                                     NetworkError, TimeoutError)

logger = logging.getLogger(__name__)

API_VERSION = "v1"
API_PREFIX = f"api/{API_VERSION}"
DEFAULT_TIMEOUT = 30.0

_LABELBOX_API_KEY = "LABELBOX_API_KEY"


class Session:

    api_key: str
    api_url: str
    base_api_url: str
    initialized: bool = False

    @classmethod
    def initialize(cls, base_api_url="https://api.labelbox.com", api_key=None):
        if api_key is None:
            if _LABELBOX_API_KEY not in os.environ:
                raise AuthenticationError("Labelbox API key not provided")
            api_key = os.environ[_LABELBOX_API_KEY]
        logger.info("Initializing Labelbox session at '%s'", base_api_url)
        cls.api_key = api_key
        cls.base_api_url = base_api_url
        cls.api_url = f"{cls.base_api_url}/{API_PREFIX}"
        cls.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % api_key,
            'X-User-Agent': f'python-sdk {SDK_VERSION}'
        }
        cls.initialized = True

    @classmethod
    def get_request(cls, uri, params=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("GET", uri, params=params, timeout=timeout)

    @classmethod
    def post_request(cls, uri, data=None, json=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("POST",
                                 uri,
                                 data=data,
                                 json=json,
                                 timeout=timeout)

    @classmethod
    def put_request(cls, uri, data=None, json=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("PUT",
                                 uri,
                                 data=data,
                                 json=json,
                                 timeout=timeout)

    @classmethod
    def patch_request(cls, uri, data=None, json=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("PATCH",
                                 uri,
                                 data=data,
                                 json=json,
                                 timeout=timeout)

    @classmethod
    def delete_request(cls, uri, params=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("DELETE", uri, params=params, timeout=timeout)

    @classmethod
    def _http_request(cls,
                      method,
                      uri,
                      params=None,
                      data=None,
                      json=None,
                      timeout=DEFAULT_TIMEOUT):
        if not cls.initialized:
            raise LabelboxError("Session has not been initialized")

        url = join_uri(cls.api_url, uri)
        try:
            request = {
                'method': method,
                'url': url,
                'headers': cls.headers,
                'data': data,
                'json': json,
                'params': params,
                'timeout': timeout
            }
            response = requests.request(**request)

        except requests.exceptions.Timeout as e:
            raise TimeoutError(str(e))
        except requests.exceptions.RequestException as e:
            logger.error("Unknown error: %s", str(e))
            raise NetworkError(e)
        except Exception as e:
            raise LabelboxError(
                "Unknown error during Client.query(): " + str(e), e)

        if response.status_code is requests.codes.no_content:
            return

        try:
            logger.debug("Response: %s", response.text)
            r_json = response.json()
        except:
            raise LabelboxError("Failed to parse response as JSON: %s" %
                                response.text)

        if response.status_code not in [
                requests.codes.ok, requests.codes.created
        ]:
            message = response.text
            cause = r_json['message']
            raise LabelboxError(message, cause)

        return r_json

    @classmethod
    def print(cls) -> str:
        return f"{cls.__name__}(base_api_url={cls.base_api_url}," \
            f"api_url={cls.api_url}," \
            f"api_key={cls.api_key}," \
            f"initialized={cls.initialized}"
