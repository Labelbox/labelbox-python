class LabelboxError(Exception):
    """Base class for exceptions."""
    pass

class AuthenticationError(LabelboxError):
    def __init__(self, message):
        self.message = message

class AuthorizationError(LabelboxError):
    def __init__(self, message):
        self.message = message

class MalformedRequestError(LabelboxError):
    def __init__(self, message):
        self.message = message

class ResourceNotFoundError(LabelboxError):
    def __init__(self, message):
        self.message = message

class InvalidAuthenticationError(LabelboxError):
    def __init__(self, message):
        self.message = message

class ValidationFailedError(LabelboxError):
    def __init__(self, message):
        self.message = message
