import re


def snake_to_camel(s):
    """ Converts a string in snake_case to camelCase. """
    return re.sub("_(\w)", lambda m: m.group(1).upper(), s)
