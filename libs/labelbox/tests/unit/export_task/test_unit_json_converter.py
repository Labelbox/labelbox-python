from unittest.mock import MagicMock

from labelbox.schema.export_task import (
    Converter,
    JsonConverter,
    Range,
    _MetadataFileInfo,
)


class TestJsonConverter:
    def test_with_correct_ndjson(self, generate_random_ndjson):
        line_count = 10
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson) + "\n"
        input_args = Converter.ConverterInputArgs(
            ctx=MagicMock(),
            file_info=_MetadataFileInfo(
                offsets=Range(start=0, end=len(file_content) - 1),
                lines=Range(start=0, end=line_count - 1),
                file="file.ndjson",
            ),
            raw_data=file_content,
        )
        with JsonConverter() as converter:
            current_offset = 0
            for idx, output in enumerate(converter.convert(input_args)):
                assert output.current_line == idx
                assert output.current_offset == current_offset
                assert output.json_str == ndjson[idx]
                current_offset += len(output.json_str) + 1

    def test_with_no_newline_at_end(self, generate_random_ndjson):
        line_count = 10
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson)
        input_args = Converter.ConverterInputArgs(
            ctx=MagicMock(),
            file_info=_MetadataFileInfo(
                offsets=Range(start=0, end=len(file_content) - 1),
                lines=Range(start=0, end=line_count - 1),
                file="file.ndjson",
            ),
            raw_data=file_content,
        )
        with JsonConverter() as converter:
            current_offset = 0
            for idx, output in enumerate(converter.convert(input_args)):
                assert output.current_line == idx
                assert output.current_offset == current_offset
                assert output.json_str == ndjson[idx]
                current_offset += len(output.json_str) + 1

    def test_from_offset(self, generate_random_ndjson):
        # testing middle of a JSON string, but not the last line
        line_count = 10
        line_start = 5
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson) + "\n"
        offset_end = len(file_content)
        skipped_bytes = 15
        current_offset = file_content.find(ndjson[line_start]) + skipped_bytes
        file_content = file_content[current_offset:]

        input_args = Converter.ConverterInputArgs(
            ctx=MagicMock(),
            file_info=_MetadataFileInfo(
                offsets=Range(start=current_offset, end=offset_end),
                lines=Range(start=line_start, end=line_count - 1),
                file="file.ndjson",
            ),
            raw_data=file_content,
        )
        with JsonConverter() as converter:
            for idx, output in enumerate(converter.convert(input_args)):
                assert output.current_line == line_start + idx
                assert output.current_offset == current_offset
                assert (
                    output.json_str == ndjson[line_start + idx][skipped_bytes:]
                )
                current_offset += len(output.json_str) + 1
                skipped_bytes = 0

    def test_from_offset_last_line(self, generate_random_ndjson):
        # testing middle of a JSON string, but not the last line
        line_count = 10
        line_start = 9
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson) + "\n"
        offset_end = len(file_content)
        skipped_bytes = 15
        current_offset = file_content.find(ndjson[line_start]) + skipped_bytes
        file_content = file_content[current_offset:]

        input_args = Converter.ConverterInputArgs(
            ctx=MagicMock(),
            file_info=_MetadataFileInfo(
                offsets=Range(start=current_offset, end=offset_end),
                lines=Range(start=line_start, end=line_count - 1),
                file="file.ndjson",
            ),
            raw_data=file_content,
        )
        with JsonConverter() as converter:
            for idx, output in enumerate(converter.convert(input_args)):
                assert output.current_line == line_start + idx
                assert output.current_offset == current_offset
                assert (
                    output.json_str == ndjson[line_start + idx][skipped_bytes:]
                )
                current_offset += len(output.json_str) + 1
                skipped_bytes = 0
