from unittest.mock import MagicMock, patch
from labelbox.schema.export_task import (
    FileRetrieverByOffset,
    _TaskContext,
    _MetadataHeader,
    StreamType,
)


class TestFileRetrieverByOffset:
    def test_by_offset_from_start(self, generate_random_ndjson, mock_response):
        line_count = 10
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson) + "\n"

        mock_client = MagicMock()
        mock_client.execute = MagicMock(
            return_value={
                "task": {
                    "exportFileFromOffset": {
                        "offsets": {"start": "0", "end": len(file_content) - 1},
                        "lines": {"start": "0", "end": str(line_count - 1)},
                        "file": "http://some-url.com/file.ndjson",
                    }
                }
            }
        )

        mock_ctx = _TaskContext(
            client=mock_client,
            task_id="task-id",
            stream_type=StreamType.RESULT,
            metadata_header=_MetadataHeader(
                total_size=len(file_content), total_lines=line_count
            ),
        )

        with patch("requests.get", return_value=mock_response(file_content)):
            retriever = FileRetrieverByOffset(mock_ctx, 0)
            info, content = retriever.get_next_chunk()
            assert info.offsets.start == 0
            assert info.offsets.end == len(file_content) - 1
            assert info.lines.start == 0
            assert info.lines.end == line_count - 1
            assert info.file == "http://some-url.com/file.ndjson"
            assert content == file_content

    def test_by_offset_from_middle(self, generate_random_ndjson, mock_response):
        line_count = 10
        ndjson = generate_random_ndjson(line_count)
        file_content = "\n".join(ndjson) + "\n"

        mock_client = MagicMock()
        mock_client.execute = MagicMock(
            return_value={
                "task": {
                    "exportFileFromOffset": {
                        "offsets": {"start": "0", "end": len(file_content) - 1},
                        "lines": {"start": "0", "end": str(line_count - 1)},
                        "file": "http://some-url.com/file.ndjson",
                    }
                }
            }
        )

        mock_ctx = _TaskContext(
            client=mock_client,
            task_id="task-id",
            stream_type=StreamType.RESULT,
            metadata_header=_MetadataHeader(
                total_size=len(file_content), total_lines=line_count
            ),
        )

        line_start = 5
        skipped_bytes = 15
        current_offset = file_content.find(ndjson[line_start]) + skipped_bytes

        with patch("requests.get", return_value=mock_response(file_content)):
            retriever = FileRetrieverByOffset(mock_ctx, current_offset)
            info, content = retriever.get_next_chunk()
            assert info.offsets.start == current_offset
            assert info.offsets.end == len(file_content) - 1
            assert info.lines.start == 5
            assert info.lines.end == line_count - 1
            assert info.file == "http://some-url.com/file.ndjson"
            assert content == file_content[current_offset:]
