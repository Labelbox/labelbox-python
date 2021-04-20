import re


def _convert(s, sep, title):
    components = re.findall(r"[A-Z][a-z0-9]*|[a-z][a-z0-9]*", s)
    components = list(map(str.lower, filter(None, components)))
    for i in range(len(components)):
        if title(i):
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
