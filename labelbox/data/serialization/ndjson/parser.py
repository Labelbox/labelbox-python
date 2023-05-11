import json


class NdjsonDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.parse_array = self._parse_array

    # def _parse_array(self, *args, **kwargs):
    #     return list(self.scan_once(*args, **kwargs))

    def decode(self, s: str, *args, **kwargs):
        lines = ','.join(s.splitlines())
        text = f"[{lines}]"  # NOTE: this is a hack to make json.loads work for ndjson
        return super().decode(text, *args, **kwargs)


def loads(ndjson_string, **kwargs) -> list:
    kwargs.setdefault('cls', NdjsonDecoder)
    return json.loads(ndjson_string, **kwargs)


def dumps(obj, **kwargs) -> str:
    lines = map(lambda obj: json.dumps(obj, **kwargs), obj)
    return '\n'.join(lines)


def reader(io_handle, **kwargs):
    for line in io_handle:
        yield json.loads(line, **kwargs)
