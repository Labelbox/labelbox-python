import time
from labelbox import DataRow


def test_export_data_rows(client, data_row, wait_for_data_row_processing):
    # Ensure created data rows are indexed
    data_row = wait_for_data_row_processing(client, data_row)
    time.sleep(7)  # temp fix for ES indexing delay

    task = DataRow.export_v2(client=client, data_rows=[data_row])
    task.wait_till_done()
    assert task.status == "COMPLETE"
    assert task.errors is None
    assert len(task.result) == 1
    assert task.result[0]["data_row"]["id"] == data_row.uid

    task = DataRow.export_v2(client=client, data_rows=[data_row.uid])
    task.wait_till_done()
    assert task.status == "COMPLETE"
    assert task.errors is None
    assert len(task.result) == 1
    assert task.result[0]["data_row"]["id"] == data_row.uid

    task = DataRow.export_v2(client=client, global_keys=[data_row.global_key])
    task.wait_till_done()
    assert task.status == "COMPLETE"
    assert task.errors is None
    assert len(task.result) == 1
    assert task.result[0]["data_row"]["id"] == data_row.uid
