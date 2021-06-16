import re
import uuid
import base36

_CUID_REGEX = r"^c[0-9a-z]{24}$"
MAX_SUPPORTED_CUID = "cy3mdbdhy3uqaqwzejcdh6akf"
MAX_SUPPORTED_UUID = "ffffffff-ffff-0fff-ffff-ffffffffffff"


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


def cuid_to_uuid(cuid: str) -> uuid.UUID:
    if not re.match(_CUID_REGEX, cuid) or cuid > MAX_SUPPORTED_CUID:
        raise ValueError("Invalid CUID: " + cuid)

    cleaned = cuid[1:]

    intermediate = 0
    for c in cleaned:
        intermediate = intermediate * 36 + int(c, 36)
    intermediate_str = f"{intermediate:x}"  #  int->str in hexadecimal

    padded = (32 - len(intermediate_str)) * '0' + intermediate_str

    return uuid.UUID("-".join((padded[1:9], padded[9:13], "0" + padded[13:16],
                               padded[16:20], padded[20:32])))


def uuid_to_cuid(uuid: uuid.UUID) -> str:
    cleaned = str(uuid).replace("-", "")

    if cleaned[12] != "0":
        raise ValueError("Invalid UUID with non-zero version hex digit")

    cleaned = cleaned[0:12] + cleaned[13:]

    intermediate = 0
    for c in cleaned:
        intermediate = intermediate * 16 + int(c, 16)
    intermediate_str = base36.dumps(intermediate)  # int->str in base36

    padded = (24 - len(intermediate_str)) * '0' + intermediate_str

    return "c" + padded
