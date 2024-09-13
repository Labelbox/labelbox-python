from unittest.mock import MagicMock

from labelbox.schema.export_task import (
    Converter,
    FileConverter,
    Range,
    StreamType,
    _MetadataFileInfo,
    _MetadataHeader,
    _TaskContext,
)


class TestFileConverter:
    def test_with_correct_ndjson(self, tmp_path, generate_random_ndjson):
        directory = tmp_path / "file-converter"
        directory.mkdir()
        line_count = 10
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson) + "\n"
        input_args = Converter.ConverterInputArgs(
            ctx=_TaskContext(
                client=MagicMock(),
                task_id="task-id",
                stream_type=StreamType.RESULT,
                metadata_header=_MetadataHeader(
                    total_size=len(file_content), total_lines=line_count
                ),
            ),
            file_info=_MetadataFileInfo(
                offsets=Range(start=0, end=len(file_content) - 1),
                lines=Range(start=0, end=line_count - 1),
                file="file.ndjson",
            ),
            raw_data=file_content,
        )
        path = directory / "output.ndjson"
        with FileConverter(file_path=path) as converter:
            for output in converter.convert(input_args):
                assert output.current_line == 0
                assert output.current_offset == 0
                assert output.file_path == path
                assert output.total_lines == line_count
                assert output.total_size == len(file_content)
                assert output.bytes_written == len(file_content)

    def test_with_no_newline_at_end(self, tmp_path, generate_random_ndjson):
        directory = tmp_path / "file-converter"
        directory.mkdir()
        line_count = 10
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson)
        input_args = Converter.ConverterInputArgs(
            ctx=_TaskContext(
                client=MagicMock(),
                task_id="task-id",
                stream_type=StreamType.RESULT,
                metadata_header=_MetadataHeader(
                    total_size=len(file_content), total_lines=line_count
                ),
            ),
            file_info=_MetadataFileInfo(
                offsets=Range(start=0, end=len(file_content) - 1),
                lines=Range(start=0, end=line_count - 1),
                file="file.ndjson",
            ),
            raw_data=file_content,
        )
        path = directory / "output.ndjson"
        with FileConverter(file_path=path) as converter:
            for output in converter.convert(input_args):
                assert output.current_line == 0
                assert output.current_offset == 0
                assert output.file_path == path
                assert output.total_lines == line_count
                assert output.total_size == len(file_content)
                assert output.bytes_written == len(file_content)
