import json

from unittest.mock import MagicMock, patch
from labelbox.schema.export_task import ExportTask

class TestExportTask:

    def test_export_task(self):
        with patch('requests.get') as mock_requests_get:
            mock_task = MagicMock()
            mock_task.client.execute.side_effect = [
                {"task": {"exportMetadataHeader": { "total_size": 1, "total_lines": 1, "lines": { "start": 0, "end": 1 }, "offsets": { "start": 0, "end": 0 }, "file": "file" } } },
                {"task": {"exportFileFromOffset": { "total_size": 1, "total_lines": 1, "lines": { "start": 0, "end": 1 }, "offsets": { "start": 0, "end": 0 }, "file": "file" } } },
            ]
            mock_task.status = "COMPLETE"
            data = {
                "data_row": {
                    "raw_data": """
                    {"raw_text":"}{"}
                    {"raw_text":"\\nbad"}   
                    """
                }
            }
            mock_requests_get.return_value.text = json.dumps(data)
            mock_requests_get.return_value.content = "b"
            export_task = ExportTask(mock_task, is_export_v2=True)
            assert export_task.result[0] == data