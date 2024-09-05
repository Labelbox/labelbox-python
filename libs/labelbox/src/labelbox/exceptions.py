import re


class LabelboxError(Exception):
    """Base class for exceptions."""

    def __init__(self, message, cause=None):
        """
        Args:
            message (str): Informative message about the exception.
            cause (Exception): The cause of the exception (an Exception
                raised by Python or another library). Optional.
        """
        super().__init__(message, cause)
        self.message = message
        self.cause = cause

    def __str__(self):
        return self.message + str(self.args)


class AuthenticationError(LabelboxError):
    """Raised when an API key fails authentication."""
    pass


class AuthorizationError(LabelboxError):
    """Raised when a user is unauthorized to perform the given request."""
    pass


class ResourceNotFoundError(LabelboxError):
    """Exception raised when a given resource is not found. """

    def __init__(self, db_object_type=None, params=None, message=None):
        """Constructor for the ResourceNotFoundException class.

        Args:
            db_object_type (type): A subtype of labelbox.schema.DbObject.
            params (dict): A dictionary of parameters identifying the sought resource.
            message (str): An optional message to include in the exception.
        """
        if message is not None:
            super().__init__(message)
        else:
            super().__init__("Resource '%s' not found for params: %r" %
                             (db_object_type.type_name(), params))
            self.db_object_type = db_object_type
            self.params = params


class ResourceConflict(LabelboxError):
    """Exception raised when a given resource conflicts with another. """
    pass


class ValidationFailedError(LabelboxError):
    """Exception raised for when a GraphQL query fails validation (query cost,
    etc.) E.g. a query that is too expensive, or depth is too deep.
    """
    pass


class InternalServerError(LabelboxError):
    """Nondescript prisma or 502 related errors.

    Meant to be retryable.

    TODO: these errors need better messages from platform
    """
    pass


class InvalidQueryError(LabelboxError):
    """ Indicates a malconstructed or unsupported query (either by GraphQL in
    general or by Labelbox specifically). This can be the result of either client
    or server side query validation. """
    pass


class UnprocessableEntityError(LabelboxError):
    """ Indicates that a resource could not be created in the server side
    due to a validation or transaction error"""
    pass


class ResourceCreationError(LabelboxError):
    """ Indicates that a resource could not be created in the server side
    due to a validation or transaction error"""
    pass


class NetworkError(LabelboxError):
    """Raised when an HTTPError occurs."""

    def __init__(self, cause):
        super().__init__(str(cause), cause)
        self.cause = cause


class TimeoutError(LabelboxError):
    """Raised when a request times-out."""
    pass


class InvalidAttributeError(LabelboxError):
    """ Raised when a field (name or Field instance) is not valid or found
    for a specific DB object type. """

    def __init__(self, db_object_type, field):
        super().__init__("Field(s) '%r' not valid on DB type '%s'" %
                         (field, db_object_type.type_name()))
        self.db_object_type = db_object_type
        self.field = field


class ApiLimitError(LabelboxError):
    """ Raised when the user performs too many requests in a short period
    of time. """
    pass


class MalformedQueryException(Exception):
    """ Raised when the user submits a malformed query."""
    pass


class UuidError(LabelboxError):
    """ Raised when there are repeat Uuid's in bulk import request."""
    pass


class InconsistentOntologyException(Exception):
    pass


class MALValidationError(LabelboxError):
    """Raised when user input is invalid for MAL imports."""
    pass


class OperationNotAllowedException(Exception):
    """Raised when user does not have permissions to a resource or has exceeded usage limit"""
    pass


class OperationNotSupportedException(Exception):
    """Raised when sdk does not support requested operation"""
    pass


class ConfidenceNotSupportedException(Exception):
    """Raised when confidence is specified for unsupported annotation type"""


class CustomMetricsNotSupportedException(Exception):
    """Raised when custom_metrics is specified for unsupported annotation type"""


class ProcessingWaitTimeout(Exception):
    """Raised when waiting for the data rows to be processed takes longer than allowed"""


def error_message_for_unparsed_graphql_error(error_string: str) -> str:
    """
    Since our client only parses certain graphql errors, this function is used to
    extract the error message from the error string when the error is not
    parsed by the client.
    """
    # Regex to find the message content
    pattern = r"'message': '([^']+)'"
    # Search for the pattern in the error string
    match = re.search(pattern, error_string)
    if match:
        error_content = match.group(1)
    else:
        error_content = "Unknown error"

    return error_content
