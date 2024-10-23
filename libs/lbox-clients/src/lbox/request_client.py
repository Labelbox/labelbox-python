# for the Labelbox Python SDK
import json
import logging
import os
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Callable, Dict, Optional

import requests
import requests.exceptions
from google.api_core import retry
from lbox import exceptions
from lbox.call_info import call_info_as_str, python_version_info  # type: ignore

logger = logging.getLogger(__name__)

_LABELBOX_API_KEY = "LABELBOX_API_KEY"


class RequestClient:
    """A Labelbox request client.

    Contains info necessary for connecting to a Labelbox server (URL,
    authentication key).
    """

    def __init__(
        self,
        sdk_version,
        api_key=None,
        endpoint="https://api.labelbox.com/graphql",
        enable_experimental=False,
        app_url="https://app.labelbox.com",
        rest_endpoint="https://api.labelbox.com/api/v1",
    ):
        """Creates and initializes a RequestClient.
        This class executes graphql and rest requests to the Labelbox server.

        Args:
            api_key (str): API key. If None, the key is obtained from the "LABELBOX_API_KEY" environment variable.
            endpoint (str): URL of the Labelbox server to connect to.
            enable_experimental (bool): Indicates whether or not to use experimental features
            app_url (str) : host url for all links to the web app
        Raises:
            exceptions.AuthenticationError: If no `api_key`
                is provided as an argument or via the environment
                variable.
        """
        if api_key is None:
            if _LABELBOX_API_KEY not in os.environ:
                raise exceptions.AuthenticationError("Labelbox API key not provided")
            api_key = os.environ[_LABELBOX_API_KEY]
        self.api_key = api_key

        self.enable_experimental = enable_experimental
        if enable_experimental:
            logger.info("Experimental features have been enabled")

        logger.info("Initializing Labelbox client at '%s'", endpoint)
        self.app_url = app_url
        self.endpoint = endpoint
        self.rest_endpoint = rest_endpoint
        self.sdk_version = sdk_version
        self._sdk_method = None
        self._connection: requests.Session = self._init_connection()

    def _init_connection(self) -> requests.Session:
        connection = requests.Session()  # using default connection pool size of 10
        connection.headers.update(self._default_headers())

        return connection

    @property
    def headers(self) -> MappingProxyType:
        return self._connection.headers

    @property
    def sdk_method(self):
        return self._sdk_method

    @sdk_method.setter
    def sdk_method(self, value):
        self._sdk_method = value

    def _default_headers(self):
        return {
            "Authorization": "Bearer %s" % self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-User-Agent": f"python-sdk {self.sdk_version}",
            "X-Python-Version": f"{python_version_info()}",
        }

    @retry.Retry(
        predicate=retry.if_exception_type(
            exceptions.InternalServerError,
            exceptions.TimeoutError,
        )
    )
    def execute(
        self,
        query=None,
        params=None,
        data=None,
        files=None,
        timeout=60.0,
        experimental=False,
        error_log_key="message",
        raise_return_resource_not_found=False,
        error_handlers: Optional[
            Dict[str, Callable[[requests.models.Response], None]]
        ] = None,
    ):
        """Sends a request to the server for the execution of the
        given query.

        Checks the response for errors and wraps errors
        in appropriate `exceptions.LabelboxError` subtypes.

        Args:
            query (str): The query to execute.
            params (dict): Query parameters referenced within the query.
            data (str): json string containing the query to execute
            files (dict): file arguments for request
            timeout (float): Max allowed time for query execution,
                in seconds.
            raise_return_resource_not_found: By default the client relies on the caller to raise the correct exception when a resource is not found.
                If this is set to True, the client will raise a ResourceNotFoundError exception automatically.
                This simplifies processing.
                We recommend to use it only of api returns a clear and well-formed error when a resource not found for a given query.
            error_handlers (dict): A dictionary mapping graphql error code to handler functions.
                Allows a caller to handle specific errors reporting in a custom way or produce more user-friendly readable messages.

        Example - custom error handler:
            >>>     def _raise_readable_errors(self, response):
            >>>         errors = response.json().get('errors', [])
            >>>         if errors:
            >>>             message = errors[0].get(
            >>>             'message', json.dumps([{
            >>>                 "errorMessage": "Unknown error"
            >>>             }]))
            >>>             errors = json.loads(message)
            >>>             error_messages = [error['errorMessage'] for error in errors]
            >>>         else:
            >>>             error_messages = ["Uknown error"]
            >>>         raise LabelboxError(". ".join(error_messages))

        Returns:
            dict, parsed JSON response.
        Raises:
            exceptions.AuthenticationError: If authentication
                failed.
            exceptions.InvalidQueryError: If `query` is not
                syntactically or semantically valid (checked server-side).
            exceptions.ApiLimitError: If the server API limit was
                exceeded. See "How to import data" in the online documentation
                to see API limits.
            exceptions.TimeoutError: If response was not received
                in `timeout` seconds.
            exceptions.NetworkError: If an unknown error occurred
                most likely due to connection issues.
            exceptions.LabelboxError: If an unknown error of any
                kind occurred.
            ValueError: If query and data are both None.
        """
        logger.debug("Query: %s, params: %r, data %r", query, params, data)

        # Convert datetimes to UTC strings.
        def convert_value(value):
            if isinstance(value, datetime):
                value = value.astimezone(timezone.utc)
                value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            return value

        if query is not None:
            if params is not None:
                params = {key: convert_value(value) for key, value in params.items()}
            data = json.dumps({"query": query, "variables": params}).encode("utf-8")
        elif data is None:
            raise ValueError("query and data cannot both be none")

        endpoint = (
            self.endpoint
            if not experimental
            else self.endpoint.replace("/graphql", "/_gql")
        )

        try:
            headers = self._connection.headers.copy()
            if files:
                del headers["Content-Type"]
                del headers["Accept"]
            headers["X-SDK-Method"] = (
                self.sdk_method if self.sdk_method else call_info_as_str()
            )

            request = requests.Request(
                "POST",
                endpoint,
                headers=headers,
                data=data,
                files=files if files else None,
            )

            prepped: requests.PreparedRequest = request.prepare()

            settings = self._connection.merge_environment_settings(
                prepped.url, {}, None, None, None
            )
            response = self._connection.send(prepped, timeout=timeout, **settings)
            logger.debug("Response: %s", response.text)
        except requests.exceptions.Timeout as e:
            raise exceptions.TimeoutError(str(e))
        except requests.exceptions.RequestException as e:
            logger.error("Unknown error: %s", str(e))
            raise exceptions.NetworkError(e)
        except Exception as e:
            raise exceptions.LabelboxError(
                "Unknown error during Client.query(): " + str(e), e
            )

        if (
            200 <= response.status_code < 300
            or response.status_code < 500
            or response.status_code >= 600
        ):
            try:
                r_json = response.json()
            except Exception:
                raise exceptions.LabelboxError(
                    "Failed to parse response as JSON: %s" % response.text
                )
        else:
            if (
                "upstream connect error or disconnect/reset before headers"
                in response.text
            ):
                raise exceptions.InternalServerError("Connection reset")
            elif response.status_code == 502:
                error_502 = "502 Bad Gateway"
                raise exceptions.InternalServerError(error_502)
            elif 500 <= response.status_code < 600:
                error_500 = f"Internal server http error {response.status_code}"
                raise exceptions.InternalServerError(error_500)

        errors = r_json.get("errors", [])

        def check_errors(keywords, *path):
            """Helper that looks for any of the given `keywords` in any of
            current errors on paths (like error[path][component][to][keyword]).
            """
            for error in errors:
                obj = error
                for path_elem in path:
                    obj = obj.get(path_elem, {})
                if obj in keywords:
                    return error
            return None

        def get_error_status_code(error: dict) -> int:
            try:
                return int(error["extensions"].get("exception").get("status"))
            except Exception:
                return 500

        if check_errors(["AUTHENTICATION_ERROR"], "extensions", "code") is not None:
            raise exceptions.AuthenticationError("Invalid API key")

        authorization_error = check_errors(
            ["AUTHORIZATION_ERROR"], "extensions", "code"
        )
        if authorization_error is not None:
            raise exceptions.AuthorizationError(authorization_error["message"])

        validation_error = check_errors(
            ["GRAPHQL_VALIDATION_FAILED"], "extensions", "code"
        )

        if validation_error is not None:
            message = validation_error["message"]
            if message == "Query complexity limit exceeded":
                raise exceptions.ValidationFailedError(message)
            else:
                raise exceptions.InvalidQueryError(message)

        graphql_error = check_errors(["GRAPHQL_PARSE_FAILED"], "extensions", "code")
        if graphql_error is not None:
            raise exceptions.InvalidQueryError(graphql_error["message"])

        # Check if API limit was exceeded
        response_msg = r_json.get("message", "")

        if response_msg.startswith("You have exceeded"):
            raise exceptions.ApiLimitError(response_msg)

        resource_not_found_error = check_errors(
            ["RESOURCE_NOT_FOUND"], "extensions", "code"
        )
        if resource_not_found_error is not None:
            if raise_return_resource_not_found:
                raise exceptions.ResourceNotFoundError(
                    message=resource_not_found_error["message"]
                )
            else:
                # Return None and let the caller methods raise an exception
                # as they already know which resource type and ID was requested
                return None

        resource_conflict_error = check_errors(
            ["RESOURCE_CONFLICT"], "extensions", "code"
        )
        if resource_conflict_error is not None:
            raise exceptions.ResourceConflict(resource_conflict_error["message"])

        malformed_request_error = check_errors(
            ["MALFORMED_REQUEST"], "extensions", "code"
        )

        error_code = "MALFORMED_REQUEST"
        if malformed_request_error is not None:
            if error_handlers and error_code in error_handlers:
                handler = error_handlers[error_code]
                handler(response)
                return None
            raise exceptions.MalformedQueryException(
                malformed_request_error[error_log_key]
            )

        # A lot of different error situations are now labeled serverside
        # as INTERNAL_SERVER_ERROR, when they are actually client errors.
        # TODO: fix this in the server API
        internal_server_error = check_errors(
            ["INTERNAL_SERVER_ERROR"], "extensions", "code"
        )
        error_code = "INTERNAL_SERVER_ERROR"

        if internal_server_error is not None:
            if error_handlers and error_code in error_handlers:
                handler = error_handlers[error_code]
                handler(response)
                return None
            message = internal_server_error.get("message")
            error_status_code = get_error_status_code(internal_server_error)
            if error_status_code == 400:
                raise exceptions.InvalidQueryError(message)
            elif error_status_code == 422:
                raise exceptions.UnprocessableEntityError(message)
            elif error_status_code == 426:
                raise exceptions.OperationNotAllowedException(message)
            elif error_status_code == 500:
                raise exceptions.LabelboxError(message)
            else:
                raise exceptions.InternalServerError(message)

        not_allowed_error = check_errors(
            ["OPERATION_NOT_ALLOWED"], "extensions", "code"
        )
        if not_allowed_error is not None:
            message = not_allowed_error.get("message")
            raise exceptions.OperationNotAllowedException(message)

        if len(errors) > 0:
            logger.warning("Unparsed errors on query execution: %r", errors)
            messages = list(
                map(
                    lambda x: {
                        "message": x["message"],
                        "code": x["extensions"]["code"],
                    },
                    errors,
                )
            )
            raise exceptions.LabelboxError("Unknown error: %s" % str(messages))

        # if we do return a proper error code, and didn't catch this above
        # reraise
        # this mainly catches a 401 for API access disabled for free tier
        # TODO: need to unify API errors to handle things more uniformly
        # in the SDK
        if response.status_code != requests.codes.ok:
            message = f"{response.status_code} {response.reason}"
            cause = r_json.get("message")
            raise exceptions.LabelboxError(message, cause)

        return r_json["data"]
