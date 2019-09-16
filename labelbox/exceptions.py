class LabelboxError(Exception):
    """Base class for exceptions."""
    def __init__(self, message, *args):
        super().__init__(*args)
        self.message = message


class AuthenticationError(LabelboxError):
    """Raised when an API key fails authentication."""
    pass


class AuthorizationError(LabelboxError):
    """Raised when a user is unauthorized to perform the given request."""
    pass


class ResourceNotFoundError(LabelboxError):
    """Exception raised when a given resource is not found. """

    def __init__(self, db_object_type, params):
        """ Constructor.
        Args:
            db_object_type (type): A labelbox.schema.DbObject subtype.
            params (dict): Dict of params identifying the sought resource.
        """
        super().__init__("Resouce '%s' not found for params: %r" % (
            db_object_type.type_name(), params))
        self.db_object_type = db_object_type
        self.params = params


class ValidationFailedError(LabelboxError):
    """Exception raised for when a GraphQL query fails validation (query cost, etc.)

       E.g. a query that is too expensive, or depth is too deep.
    """
    pass


class InvalidQueryError(LabelboxError):
    """ Indicates a malconstructed or unsupported query (either by GraphQL in
    general or by Labelbox specifically). This can be the result of either client
    or server side query validation. """
    pass


class NetworkError(LabelboxError):
    """Raised when an HTTPError occurs."""
    def __init__(self, cause, message=None):
        if message is None:
            message = str(cause)
        super().__init__(message)
        self.cause = cause


class TimeoutError(LabelboxError):
    """Raised when a request times-out."""
    pass


class InvalidAttributeError(LabelboxError):
    """ Raised when a field (name or Field instance) is not valid or found
    for a specific DB object type. """
    def __init__(self, db_object_type, field):
        super().__init__("Field(s) '%r' not valid on DB type '%s'" % (
            field, db_object_type.type_name()))
        self.db_object_type = db_object_type
        self.field = field


class ApiLimitError(LabelboxError):
    """ Raised when the user performs too many requests in a short period
    of time. """
    pass
