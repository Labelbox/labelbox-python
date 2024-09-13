import json


class NdjsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def decode(self, s: str, *args, **kwargs):
        lines = ",".join(s.splitlines())
        text = f"[{lines}]"  # NOTE: this is a hack to make json.loads work for ndjson
        return super().decode(text, *args, **kwargs)


def loads(ndjson_string, **kwargs) -> list:
    kwargs.setdefault("cls", NdjsonDecoder)
    return json.loads(ndjson_string, **kwargs)


def dumps(obj, **kwargs):
    lines = map(lambda obj: json.dumps(obj, **kwargs), obj)
    return "\n".join(lines)


def dump(obj, io, **kwargs):
    lines = dumps(obj, **kwargs)
    io.write(lines)


def reader(io_handle, **kwargs):
    for line in io_handle:
        yield json.loads(line, **kwargs)
