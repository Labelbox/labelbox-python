import ast
from io import StringIO

from labelbox import parser


def test_loads(ndjson_content):
    expected_line, expected_objects = ndjson_content
    parsed_line = parser.loads(expected_line)

    assert parsed_line == expected_objects
    assert parser.dumps(parsed_line) == expected_line


def test_loads_bytes(ndjson_content):
    expected_line, expected_objects = ndjson_content

    bytes_line = expected_line.encode('utf-8')
    parsed_line = parser.loads(bytes_line)

    assert parsed_line == expected_objects
    assert parser.dumps(parsed_line) == expected_line


def test_reader_stringio(ndjson_content):
    line, ndjson_objects = ndjson_content

    text_io = StringIO(line)
    parsed_arr = []
    reader = parser.reader(text_io)
    for _, r in enumerate(reader):
        parsed_arr.append(r)
    assert parsed_arr == ndjson_objects


def test_non_ascii_new_line(ndjson_content_with_nonascii_and_line_breaks):
    line, expected_objects = ndjson_content_with_nonascii_and_line_breaks
    parsed = parser.loads(line)

    assert parsed == expected_objects

    # NOTE: json parser converts unicode chars to unicode literals by default and this is a good practice
    #   but it is not what we want here since we want to compare the strings with actual unicode chars
    assert ast.literal_eval("'" + parser.dumps(parsed) + "'") == line
