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
        return self.message


class AuthenticationError(LabelboxError):
    """Raised when an API key fails authentication."""
    pass


class ResourceNotFoundError(LabelboxError):
    """Exception raised when a given resource is not found. """
    pass


class NetworkError(LabelboxError):
    """Raised when an HTTPError occurs."""

    def __init__(self, cause):
        super().__init__(str(cause), cause)
        self.cause = cause


class TimeoutError(LabelboxError):
    """Raised when a request times-out."""
    pass
