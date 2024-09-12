import json
import uuid
from unittest.mock import patch

import pytest

from labelbox.schema.asset_attachment import AttachmentType
from labelbox.schema.identifiable import UniqueId, GlobalKey


class TestDataRowUpsert:
    @pytest.fixture
    def all_inclusive_data_row(self, dataset, image_url):
        dr = dataset.create_data_row(
            row_data=image_url,
            external_id="ex1",
            global_key=str(uuid.uuid4()),
            metadata_fields=[
                {"name": "tag", "value": "tag_string"},
                {"name": "split", "value": "train"},
            ],
            attachments=[
                {"type": "RAW_TEXT", "name": "att1", "value": "test1"},
                {
                    "type": "IMAGE",
                    "name": "att2",
                    "value": "https://storage.googleapis.com/labelbox-sample-datasets/Docs/disease_attachment.jpeg",
                },
                {
                    "type": "PDF_URL",
                    "name": "att3",
                    "value": "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf",
                },
            ],
        )
        return dr

    @pytest.mark.order(1)
    def test_create_data_row_with_auto_key(self, dataset, image_url):
        task = dataset.upsert_data_rows([{"row_data": image_url}])
        task.wait_till_done()
        assert len(list(dataset.data_rows())) == 1

    def test_create_data_row_with_upsert(self, client, dataset, image_url):
        gkey = str(uuid.uuid4())
        task = dataset.upsert_data_rows(
            [
                {
                    "row_data": image_url,
                    "global_key": gkey,
                    "external_id": "ex1",
                    "attachments": [
                        {
                            "type": AttachmentType.RAW_TEXT,
                            "name": "att1",
                            "value": "test1",
                        },
                        {
                            "type": AttachmentType.IMAGE,
                            "name": "att2",
                            "value": "https://storage.googleapis.com/labelbox-sample-datasets/Docs/disease_attachment.jpeg",
                        },
                        {
                            "type": AttachmentType.PDF_URL,
                            "name": "att3",
                            "value": "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf",
                        },
                    ],
                    "metadata": [
                        {"name": "tag", "value": "updated tag"},
                        {"name": "split", "value": "train"},
                    ],
                }
            ]
        )
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row_by_global_key(gkey)

        assert dr is not None
        assert dr.row_data == image_url
        assert dr.global_key == gkey
        assert dr.external_id == "ex1"

        attachments = list(dr.attachments())
        assert len(attachments) == 3
        assert attachments[0].attachment_name == "att1"
        assert attachments[0].attachment_type == AttachmentType.RAW_TEXT
        assert attachments[0].attachment_value == "test1"

        assert attachments[1].attachment_name == "att2"
        assert attachments[1].attachment_type == AttachmentType.IMAGE
        assert (
            attachments[1].attachment_value
            == "https://storage.googleapis.com/labelbox-sample-datasets/Docs/disease_attachment.jpeg"
        )

        assert attachments[2].attachment_name == "att3"
        assert attachments[2].attachment_type == AttachmentType.PDF_URL
        assert (
            attachments[2].attachment_value
            == "https://storage.googleapis.com/labelbox-datasets/arxiv-pdf/data/99-word-token-pdfs/0801.3483.pdf"
        )

        assert len(dr.metadata_fields) == 2
        assert dr.metadata_fields[0]["name"] == "tag"
        assert dr.metadata_fields[0]["value"] == "updated tag"
        assert dr.metadata_fields[1]["name"] == "split"
        assert dr.metadata_fields[1]["value"] == "train"

    def test_update_data_row_fields_with_upsert(
        self, client, dataset, image_url
    ):
        gkey = str(uuid.uuid4())
        dr = dataset.create_data_row(
            row_data=image_url, external_id="ex1", global_key=gkey
        )
        task = dataset.upsert_data_rows(
            [
                {
                    "key": UniqueId(dr.uid),
                    "external_id": "ex1_updated",
                    "global_key": f"{gkey}_updated",
                }
            ]
        )
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row(dr.uid)
        assert dr is not None
        assert dr.external_id == "ex1_updated"
        assert dr.global_key == f"{gkey}_updated"

    def test_update_data_row_fields_with_upsert_by_global_key(
        self, client, dataset, image_url
    ):
        gkey = str(uuid.uuid4())
        dr = dataset.create_data_row(
            row_data=image_url, external_id="ex1", global_key=gkey
        )
        task = dataset.upsert_data_rows(
            [
                {
                    "key": GlobalKey(dr.global_key),
                    "external_id": "ex1_updated",
                    "global_key": f"{gkey}_updated",
                }
            ]
        )
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row(dr.uid)
        assert dr is not None
        assert dr.external_id == "ex1_updated"
        assert dr.global_key == f"{gkey}_updated"

    def test_update_attachments_with_upsert(
        self, client, all_inclusive_data_row, dataset
    ):
        dr = all_inclusive_data_row
        task = dataset.upsert_data_rows(
            [
                {
                    "key": UniqueId(dr.uid),
                    "row_data": dr.row_data,
                    "attachments": [
                        {
                            "type": AttachmentType.RAW_TEXT,
                            "name": "att1",
                            "value": "test",
                        }
                    ],
                }
            ]
        )
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row(dr.uid)
        assert dr is not None
        attachments = list(dr.attachments())
        assert len(attachments) == 1
        assert attachments[0].attachment_name == "att1"

    def test_update_metadata_with_upsert(
        self, client, all_inclusive_data_row, dataset
    ):
        dr = all_inclusive_data_row
        task = dataset.upsert_data_rows(
            [
                {
                    "key": GlobalKey(dr.global_key),
                    "row_data": dr.row_data,
                    "metadata": [
                        {"name": "tag", "value": "updated tag"},
                        {"name": "split", "value": "train"},
                    ],
                }
            ]
        )
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row(dr.uid)
        assert dr is not None
        assert len(dr.metadata_fields) == 2
        assert dr.metadata_fields[0]["name"] == "tag"
        assert dr.metadata_fields[0]["value"] == "updated tag"
        assert dr.metadata_fields[1]["name"] == "split"
        assert dr.metadata_fields[1]["value"] == "train"

    def test_multiple_chunks(self, client, dataset, image_url):
        mocked_chunk_size = 300
        with patch(
            "labelbox.client.Client.upload_data", wraps=client.upload_data
        ) as spy_some_function:
            with patch(
                "labelbox.schema.dataset.UPSERT_CHUNK_SIZE_BYTES",
                new=mocked_chunk_size,
            ):
                task = dataset.upsert_data_rows(
                    [{"row_data": image_url} for i in range(10)]
                )
                task.wait_till_done()
                assert len(list(dataset.data_rows())) == 10
                assert (
                    spy_some_function.call_count == 11
                )  # one per each data row + manifest

                first_call_args, _ = spy_some_function.call_args_list[0]
                first_chunk_content = first_call_args[0]
                data = json.loads(first_chunk_content)
                """
                Each chunk but the last will have 3 items, the last will have 1.
                As the chunks are processed async, we cannot be sure of the order of the calls.
                """
                assert len(data) in {1, 3}

                last_call_args, _ = spy_some_function.call_args_list[-1]
                manifest_content = last_call_args[0].decode("utf-8")
                data = json.loads(manifest_content)
                assert data["source"] == "SDK"
                assert data["item_count"] == 10
                assert len(data["chunk_uris"]) == 10

    def test_upsert_embedded_row_data(self, dataset):
        pdf_url = "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/0801.3483.pdf"
        task = dataset.upsert_data_rows(
            [
                {
                    "row_data": {
                        "pdf_url": pdf_url,
                        "text_layer_url": "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/0801.3483-lb-textlayer.json",
                    },
                    "media_type": "PDF",
                }
            ]
        )
        task.wait_till_done()
        data_rows = list(dataset.data_rows())
        assert len(data_rows) == 1
        assert data_rows[0].row_data == pdf_url

    def test_upsert_duplicate_global_key_error(self, dataset, image_url):
        gkey = str(uuid.uuid4())
        task = dataset.upsert_data_rows(
            [
                {"row_data": image_url, "global_key": gkey},
                {"row_data": image_url, "global_key": gkey},
            ]
        )
        task.wait_till_done()
        assert task.status == "COMPLETE"
        assert task.errors is not None
        assert len(task.errors) == 1  # one data row was created, one failed
        assert f"Duplicate global key: '{gkey}'" in task.errors[0]["message"]

    def test_upsert_empty_items(self, dataset):
        items = [{"key": GlobalKey("foo")}]
        with pytest.raises(ValueError) as e_info:
            dataset.upsert_data_rows(items)
        e_info.match(r"The following items have an empty payload: \['foo'\]")
