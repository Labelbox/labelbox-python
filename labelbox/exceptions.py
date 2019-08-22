class LabelboxError(Exception):
    """Base class for exceptions."""
    def __init__(self, message):
        self.message = message

class AuthenticationError(LabelboxError):
    """Raised when an API key fails authentication."""
    pass

class AuthorizationError(LabelboxError):
    """Raised when a user is unauthorized to perform the given request."""
    pass

class MalformedRequestError(LabelboxError):
    """Raised when an invalid request is made."""
    pass

class ResourceNotFoundError(LabelboxError):
    """Exception raised when a given resource is not found. """
    pass

class ValidationFailedError(LabelboxError):
    """Exception raised for when a GraphQL query fails validation (query cost, etc.)

       E.g. a query that is too expensive, or depth is too deep.
    """
    pass

class NetworkError(LabelboxError):
    """Raised when an HTTPError occurs."""
    def __init__(self, cause, message):
        super(NetworkError, self).__init__(message)
        self.cause = cause
