import json
import random

from labelbox import ExportTask, StreamType, JsonConverter


class TestExportEmbeddings:

    def test_export_embeddings_precomputed(self, client, dataset, environ,
                                           image_url):
        data_row_specs = [{
            "row_data": image_url,
            "external_id": "image",
        }]
        task = dataset.create_data_rows(data_row_specs)
        task.wait_till_done()
        export_task = dataset.export(params={"embeddings": True})
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False

        results = []
        export_task.get_stream(converter=JsonConverter(),
                               stream_type=StreamType.RESULT).start(
                                   stream_handler=lambda output: results.append(
                                       json.loads(output.json_str)))

        assert len(results) == len(data_row_specs)

        result = results[0]
        assert "embeddings" in result
        assert len(result["embeddings"]) > 0
        assert result["embeddings"][0][
            "name"] == "Image Embedding V2 (CLIP ViT-B/32)"
        assert len(result["embeddings"][0]["values"]) == 1

    def test_export_embeddings_custom(self, client, dataset, image_url,
                                      embedding):
        vector = [random.uniform(1.0, 2.0) for _ in range(embedding.dims)]
        dataset.create_data_row(
            row_data=image_url,
            embeddings=[{
                "embedding_id": embedding.id,
                "vector": vector,
            }],
        )

        export_task = dataset.export(params={"embeddings": True})
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False

        results = []
        export_task.get_stream(converter=JsonConverter(),
                               stream_type=StreamType.RESULT).start(
                                   stream_handler=lambda output: results.append(
                                       json.loads(output.json_str)))

        assert len(results) == 1
        assert "embeddings" in results[0]
        assert (len(results[0]["embeddings"])
                >= 1)  # should at least contain the custom embedding
        for embedding in results[0]["embeddings"]:
            if embedding["id"] == embedding.id:
                assert embedding["name"] == embedding.name
                assert embedding["dimensions"] == embedding.dims
                assert embedding["is_custom"] == True
                assert len(embedding["values"]) == 1
                assert embedding["values"][0]["value"] == vector
