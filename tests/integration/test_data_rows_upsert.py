from labelbox.schema.asset_attachment import AttachmentType
from labelbox.schema.data_row import DataRowUpsertItem, DataRowKey, DataRowSpec, KeyType, DataRowAttachmentSpec


class TestDataRowUpsert:

    def test_create_data_row(self, client, dataset, image_url):
        task = dataset.upsert_data_rows([
            DataRowSpec(dataset_id=dataset.uid,
                        row_data=image_url,
                        global_key="gkey123")
        ])
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row_by_global_key("gkey123")
        assert dr is not None
        assert dr.row_data == image_url
        assert dr.global_key == "gkey123"

    def test_update_fields_by_data_row_id(self, client, dataset, image_url):
        dr = dataset.create_data_row(row_data=image_url,
                                     external_id="ex1",
                                     global_key="gk1")
        task = dataset.upsert_data_rows([
            DataRowSpec(key=DataRowKey(value=dr.uid, type=KeyType.ID),
                        dataset_id=dataset.uid,
                        external_id="ex1_updated",
                        global_key="gk1_updated")
        ])
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row(dr.uid)
        assert dr is not None
        assert dr.external_id == "ex1_updated"
        assert dr.global_key == "gk1_updated"

    def test_update_fields_by_global_key(self, client, dataset, image_url):
        dr = dataset.create_data_row(row_data=image_url,
                                     external_id="ex1",
                                     global_key="gk1")
        task = dataset.upsert_data_rows([
            DataRowSpec(key=DataRowKey(value=dr.global_key, type=KeyType.GKEY),
                        dataset_id=dataset.uid,
                        external_id="ex1_updated",
                        global_key="gk1_updated")
        ])
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row(dr.uid)
        assert dr is not None
        assert dr.external_id == "ex1_updated"
        assert dr.global_key == "gk1_updated"

    def test_upsrt(self, client, image_url):
        ds = list(client.get_datasets())[0]
        task = ds.create_data_rows([{"row_data": image_url}])
        task.wait_till_done()
        assert task.status == "COMPLETE"
        drs = list(ds.data_rows())
        print(drs)
        dr = drs[0]
        task = ds.upsert_data_rows([
            DataRowSpec(key=DataRowKey(value=dr.uid, type=KeyType.ID),
                        dataset_id=ds.uid,
                        row_data=dr.row_data,
                        attachments=[
                            DataRowAttachmentSpec(type=AttachmentType.RAW_TEXT,
                                                  name="att1",
                                                  value="test")
                        ])
        ])
        task.wait_till_done()
        assert task.status == "COMPLETE"
        dr = client.get_data_row(dr.uid)
        assert dr is not None
        attachments = list(dr.attachments())
        assert len(attachments) == 1
        assert attachments[0].attachment_type == AttachmentType.RAW_TEXT
        assert attachments[0].attachment_value == "test"
        assert attachments[0].attachment_name == "att1"
