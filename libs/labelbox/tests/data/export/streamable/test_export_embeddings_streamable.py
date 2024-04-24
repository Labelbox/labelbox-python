import json
import random

from labelbox import StreamType, JsonConverter


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
        import_task = dataset.create_data_rows([{
            "row_data": image_url,
            "embeddings": [{
                "embedding_id": embedding.id,
                "vector": vector,
            }],
        }])
        import_task.wait_till_done()
        assert import_task.status == "COMPLETE"

        export_task = dataset.export(params={"embeddings": True})
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
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
        for emb in results[0]["embeddings"]:
            if emb["id"] == embedding.id:
                assert emb["name"] == embedding.name
                assert emb["dimensions"] == embedding.dims
                assert emb["is_custom"] == True
                assert len(emb["values"]) == 1
                assert emb["values"][0]["value"] == vector
