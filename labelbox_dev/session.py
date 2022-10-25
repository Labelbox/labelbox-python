import logging
import os

import requests
import requests.exceptions

import labelbox.exceptions
from labelbox_dev import __version__ as SDK_VERSION

logger = logging.getLogger(__name__)


API_VERSION = "v1"
API_PREFIX = f"api/{API_VERSION}"
DEFAULT_TIMEOUT = 30.0

_LABELBOX_API_KEY = "LABELBOX_API_KEY"


class Session:

    @classmethod
    def initialize(cls, base_api_url="https://api.labelbox.com", api_key=None):
        if api_key is None:
            if _LABELBOX_API_KEY not in os.environ:
                raise labelbox.exceptions.AuthenticationError(
                    "Labelbox API key not provided")
            api_key = os.environ[_LABELBOX_API_KEY]
        logger.info("Initializing Labelbox session at '%s'", base_api_url)
        cls.api_key = api_key
        cls.base_api_url = base_api_url
        cls.api_url = f"{cls.base_api_url}/{API_PREFIX}"
        cls.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % api_key,
            'X-User-Agent': f'python-sdk {SDK_VERSION}'
        }
        cls.initialized = True

    @classmethod
    def get_request(cls, uri, params=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("GET",
                                  uri,
                                  params=params,
                                  timeout=timeout)

    @classmethod
    def post_request(cls, uri, data=None, json=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("POST", uri, data=data, json=json, timeout=timeout)

    @classmethod
    def put_request(cls, uri, data=None, json=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("PUT", uri, data=data, json=json, timeout=timeout)

    @classmethod
    def patch_request(cls, uri, data=None, json=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("PATCH", uri, data=data, json=json, timeout=timeout)

    @classmethod
    def delete_request(cls, uri, params=None, timeout=DEFAULT_TIMEOUT):
        return cls._http_request("DELETE",
                                  uri,
                                  params=params,
                                  timeout=timeout)

    @classmethod
    def _http_request(cls, 
                      method,
                      uri,
                      params=None,
                      data=None,
                      json=None,
                      timeout=DEFAULT_TIMEOUT):
        if uri.startswith('/'):
            uri = uri.lstrip('/')
        try:
            request = {
                'method': method,
                'url': f"{cls.api_url}/{uri}",
                'headers': cls.headers,
                'data': data,
                'json': json,
                'params': params,
                'timeout': timeout
            }
            print(request)
            response = requests.request(**request)

        except requests.exceptions.Timeout as e:
            raise labelbox.exceptions.TimeoutError(str(e))
        except requests.exceptions.RequestException as e:
            logger.error("Unknown error: %s", str(e))
            raise labelbox.exceptions.NetworkError(e)
        except Exception as e:
            raise labelbox.exceptions.LabelboxError(
                "Unknown error during Client.query(): " + str(e), e)

        try:
            r_json = response.json()
        except:
            raise labelbox.exceptions.LabelboxError(
                "Failed to parse response as JSON: %s" % response.text)

        return r_json
