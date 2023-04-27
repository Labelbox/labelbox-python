from io import FileIO, StringIO
import json
from typing import Iterable, Union


def loads(ndjson_string: str, **kwargs) -> list:
    # NOTE: the consequence of this line would be conversion of 'literal' line breaks to commas
    lines = ','.join(ndjson_string.splitlines())
    text = f"[{lines}]"  # NOTE: this is a hack to make json.loads work for ndjson
    return json.loads(text, **kwargs)


def dumps(obj: list, **kwargs) -> str:
    lines = map(lambda obj: json.dumps(obj, **kwargs), obj)
    return '\n'.join(lines)


def reader(io_handle: Union[StringIO, FileIO, Iterable], **kwargs):
    for line in io_handle:
        yield json.loads(line, **kwargs)
