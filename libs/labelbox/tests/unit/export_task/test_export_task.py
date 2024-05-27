import json
import pytest

from unittest.mock import MagicMock, patch
from labelbox.schema.export_task import ExportTask


class TestExportTask:

    def test_export_task(self):
        with patch('requests.get') as mock_requests_get:
            mock_task = MagicMock()
            mock_task.client.execute.side_effect = [
                {
                    "task": {
                        "exportMetadataHeader": {
                            "total_size": 1,
                            "total_lines": 1,
                            "lines": {
                                "start": 0,
                                "end": 1
                            },
                            "offsets": {
                                "start": 0,
                                "end": 0
                            },
                            "file": "file"
                        }
                    }
                },
                {
                    "task": {
                        "exportFileFromOffset": {
                            "total_size": 1,
                            "total_lines": 1,
                            "lines": {
                                "start": 0,
                                "end": 1
                            },
                            "offsets": {
                                "start": 0,
                                "end": 0
                            },
                            "file": "file"
                        }
                    }
                },
            ]
            mock_task.status = "COMPLETE"
            data = {
                "data_row": {
                    "raw_data":
                        """
                    {"raw_text":"}{"}
                    {"raw_text":"\\nbad"}   
                    """
                }
            }
            mock_requests_get.return_value.text = json.dumps(data)
            mock_requests_get.return_value.content = "b"
            export_task = ExportTask(mock_task, is_export_v2=True)
            assert export_task.result[0] == data

    def test_get_buffered_stream_complete(self):
        with pytest.raises(ExportTask.ExportTaskException):
            mock_task = MagicMock()
            mock_task.status = "FAILED"
            export_task = ExportTask(mock_task, is_export_v2=True)
            export_task.get_buffered_stream()

    def test_get_buffered_stream_failed(self):
        with pytest.raises(ExportTask.ExportTaskException):
            mock_task = MagicMock()
            mock_task.status = "INPROGRESS"
            export_task = ExportTask(mock_task, is_export_v2=True)
            export_task.get_buffered_stream()

    def test_get_buffered_stream(self):
        with patch('requests.get') as mock_requests_get:
            mock_task = MagicMock()
            mock_task.client.execute.side_effect = [
                {
                    "task": {
                        "exportMetadataHeader": {
                            "total_size": 1,
                            "total_lines": 1,
                            "lines": {
                                "start": 0,
                                "end": 1
                            },
                            "offsets": {
                                "start": 0,
                                "end": 0
                            },
                            "file": "file"
                        }
                    }
                },
                {
                    "task": {
                        "exportFileFromOffset": {
                            "total_size": 1,
                            "total_lines": 1,
                            "lines": {
                                "start": 0,
                                "end": 1
                            },
                            "offsets": {
                                "start": 0,
                                "end": 0
                            },
                            "file": "file"
                        }
                    }
                },
            ]
            mock_task.status = "COMPLETE"
            data = {
                "data_row": {
                    "raw_data":
                        """
                    {"raw_text":"}{"}
                    {"raw_text":"\\nbad"}
                    """
                }
            }
            mock_requests_get.return_value.text = json.dumps(data)
            mock_requests_get.return_value.content = "b"
            export_task = ExportTask(mock_task, is_export_v2=True)
            output_data = []
            export_task.get_buffered_stream().start(stream_handler=lambda x: output_data.append(x.json))
            assert data == output_data[0]

    def test_export_task_bad_offsets(self):
        with patch('requests.get') as mock_requests_get:
            mock_task = MagicMock()
            mock_task.client.execute.side_effect = [
                {
                    "task": {
                        "exportMetadataHeader": {
                            "total_size": 1,
                            "total_lines": 1,
                            "lines": {
                                "start": 0,
                                "end": 1
                            },
                            "offsets": {
                                "start": 0,
                                "end": 0
                            },
                            "file": "file"
                        }
                    }
                },
                {
                    "task": {
                        "exportFileFromOffset": {
                            "total_size": 1,
                            "total_lines": 1,
                            "lines": {
                                "start": 0,
                                "end": 1
                            },
                            "offsets": {
                                "start": 0,
                                "end": 0
                            },
                            "file": "file"
                        }
                    }
                },
            ]
            mock_task.status = "COMPLETE"
            data = {
                "data_row": {
                    "id":
                        "clwb6wvpv3mpx0712aafl9m00",
                    "external_id":
                        "43cdad5e-1fcf-450d-ad72-df4460edf973",
                    "global_key":
                        "9ab56c5a-5c2f-45ae-8e21-e53eb415cefe",
                    "row_data":
                        "{\"type\":\"application/vnd.labelbox.conversational\",\"version\":1,\"messages\":[{\"messageId\":\"message-0\",\"timestampUsec\":1530718491,\"content\":\"The minimum value of $3 \\\\cos x + 4 \\\\sin x + 8$ is\",\"user\":{\"userId\":\"prompt\",\"name\":\"prompt\"},\"align\":\"left\",\"canLabel\":true}],\"modelOutputs\":[{\"title\":\"Response 1\",\"content\":\"To find the minimum value of the expression $3 \\\\cos x + 4 \\\\sin x + 8$, we can use the fact that $a\\\\cos x+b\\\\sin x=\\\\sqrt{a^2+b^2}\\\\left(\\\\frac{a}{\\\\sqrt{a^2+b^2}}\\\\cos x+\\\\frac{b}{\\\\sqrt{a^2+b^2}}\\\\sin x\\\\right)$. This allows us to rewrite the expression as:\\n\\n$3\\\\cos x+4\\\\sin x+8=\\\\sqrt{3^2+4^2}\\\\left(\\\\frac{3}{\\\\sqrt{3^2+4^2}}\\\\cos x+\\\\frac{4}{\\\\sqrt{3^2+4^2}}\\\\sin x\\\\right)+8=5\\\\left(\\\\frac{3}{5}\\\\cos x+\\\\frac{4}{5}\\\\sin x\\\\right)+8$\\n\\nNow, let's consider the expression $\\\\frac{3}{5}\\\\cos x+\\\\frac{4}{5}\\\\sin x$. Since $\\\\left(\\\\frac{3}{5}\\\\right)^2+\\\\left(\\\\frac{4}{5}\\\\right)^2=1$, we can write $\\\\frac{3}{5}=\\\\cos\\\\theta$ and $\\\\frac{4}{5}=\\\\sin\\\\theta$ for some angle $\\\\theta$. Then:\\n\\n$\\\\frac{3}{5}\\\\cos x+\\\\frac{4}{5}\\\\sin x=\\\\cos\\\\theta\\\\cos x+\\\\sin\\\\theta\\\\sin x=\\\\cos(x-\\\\theta)$\\n\\nSo, the original expression can be written as:\\n\\n$5\\\\cos(x-\\\\theta)+8$\\n\\nSince the minimum value of $\\\\cos(x-\\\\theta)$ is $-1$, the minimum value of the original expression is:\\n\\n$5(-1)+8=-5+8=3$\\n\\nTherefore, the minimum value of $3\\\\cos x + 4\\\\sin x + 8$ is $\\\\boxed{3}$.\",\"modelConfigName\":\"null\"},{\"title\":\"Response 2\",\"content\":\"A nice math question!\\n\\nTo find the minimum value of $3 \\\\cos x + 4 \\\\sin x + 8$, we can use the fact that $a\\\\cos x + b\\\\sin x = \\\\sqrt{a^2 + b^2} \\\\cos(x - \\\\alpha)$, where $\\\\alpha = \\\\tan^{-1}\\\\left(\\\\frac{b}{a}\\\\right)$.\\n\\nIn this case, $a = 3$ and $b = 4$, so $\\\\alpha = \\\\tan^{-1}\\\\left(\\\\frac{4}{3}\\\\right)$.\\n\\nSo, we have:\\n\\n$$3 \\\\cos x + 4 \\\\sin x + 8 = \\\\sqrt{3^2 + 4^2} \\\\cos(x - \\\\alpha) + 8 = 5 \\\\cos(x - \\\\alpha) + 8$$\\n\\nNow, the minimum value of $\\\\cos(x - \\\\alpha)$ is $-1$, so the minimum value of $5 \\\\cos(x - \\\\alpha) + 8$ is:\\n\\n$$5(-1) + 8 = -5 + 8 = 3$$\\n\\nTherefore, the minimum value of $3 \\\\cos x + 4 \\\\sin x + 8$ is $\\\\boxed{3}$.\\n\\nLet me know if you have any questions or need further clarification!\",\"modelConfigName\":\"null\"}]}"
                },
                "media_attributes": {
                    "asset_type": "conversational",
                    "mime_type": "application/vnd.labelbox.conversational",
                    "labelable_ids": ["message-0"],
                    "message_count": 1
                }
            }
            mock_requests_get.return_value.text = json.dumps(data)
            mock_requests_get.return_value.content = "b"
            export_task = ExportTask(mock_task, is_export_v2=True)
            assert export_task.result[0] == data
