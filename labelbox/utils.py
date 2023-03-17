import re
from urllib.parse import urlparse
from pydantic import BaseModel

UPPERCASE_COMPONENTS = ['uri', 'rgb']


def _convert(s, sep, title):
    components = re.findall(r"[A-Z][a-z0-9]*|[a-z][a-z0-9]*", s)
    components = list(map(str.lower, filter(None, components)))
    for i in range(len(components)):
        if components[i] in UPPERCASE_COMPONENTS:
            components[i] = components[i].upper()
        elif title(i):
            components[i] = components[i][0].upper() + components[i][1:]
    return sep.join(components)


def camel_case(s):
    """ Converts a string in [snake|camel|title]case to camelCase. """
    return _convert(s, "", lambda i: i > 0)


def title_case(s):
    """ Converts a string in [snake|camel|title]case to TitleCase. """
    return _convert(s, "", lambda i: True)


def snake_case(s):
    """ Converts a string in [snake|camel|title]case to snake_case. """
    return _convert(s, "_", lambda i: False)


def is_exactly_one_set(x, y):
    return not (bool(x) == bool(y))


def is_valid_uri(uri):
    try:
        result = urlparse(uri)
        return all([result.scheme, result.netloc])
    except:
        return False


class _CamelCaseMixin(BaseModel):

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case


class _NoCoercionMixin:
    """
    When using Unions in type annotations, pydantic will try to coerce the type
    of the object to the type of the first Union member. Which results in
    uninteded behavior.

    This mixin uses a class_name discriminator field to prevent pydantic from
    corecing the type of the object. Add a class_name field to the class you 
    want to discrimniate and use this mixin class to remove the discriminator
    when serializing the object.

    Example:
        class ConversationData(BaseData, _NoCoercionMixin):
            class_name: Literal["ConversationData"] = "ConversationData"

    """

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        res.pop('class_name')
        return res
