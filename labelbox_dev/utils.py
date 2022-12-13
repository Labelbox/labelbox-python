import json
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


def keys_to_snake_case(d):
    return {snake_case(key): value for key, value in d.items()}


def format_json_to_snake_case(j):
    formatted = {}
    for key, value in keys_to_snake_case(j).items():
        if isinstance(value, dict):
            formatted[key] = keys_to_snake_case(value)
        elif isinstance(value, list):
            formatted[key] = [keys_to_snake_case(element) for element in value]
        else:
            formatted[key] = value
    return formatted
