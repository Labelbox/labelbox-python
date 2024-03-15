import pytest


@pytest.mark.parametrize('data_rows', [3], indirect=True)
def test_catalog_export_v2(client, export_v2_test_helpers, data_rows):
    datarow_filter_size = 2
    data_row_ids = [dr.uid for dr in data_rows]

    params = {"performance_details": False, "label_details": False}
    filters = {"data_row_ids": data_row_ids[:datarow_filter_size]}

    task_results = export_v2_test_helpers.run_catalog_export_v2_task(
        client, filters=filters, params=params)

    # only 2 datarows should be exported
    assert len(task_results) == datarow_filter_size
    # only filtered datarows should be exported
    assert set([dr['data_row']['id'] for dr in task_results
               ]) == set(data_row_ids[:datarow_filter_size])
