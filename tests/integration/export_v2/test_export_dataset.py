import pytest


@pytest.mark.parametrize('data_rows', [3], indirect=True)
def test_dataset_export_v2(export_v2_test_helpers, dataset, data_rows):
    data_row_ids = [dr.uid for dr in data_rows]
    params = {"performance_details": False, "label_details": False}
    task_results = export_v2_test_helpers.run_dataset_export_v2_task(
        dataset, params=params)
    assert len(task_results) == len(data_row_ids)
    assert set([dr['data_row']['id'] for dr in task_results
               ]) == set(data_row_ids)

    # testing with a datarow ids filter
    datarow_filter_size = 2
    data_row_ids = [dr.uid for dr in data_rows]

    params = {"performance_details": False, "label_details": False}
    filters = {"data_row_ids": data_row_ids[:datarow_filter_size]}

    task_results = export_v2_test_helpers.run_dataset_export_v2_task(
        dataset, filters=filters, params=params)

    # only 2 datarows should be exported
    assert len(task_results) == datarow_filter_size
    # only filtered datarows should be exported
    assert set([dr['data_row']['id'] for dr in task_results
               ]) == set(data_row_ids[:datarow_filter_size])

    # testing with a global key and a datarow id filter
    datarow_filter_size = 2
    global_keys = [dr.global_key for dr in data_rows]

    params = {"performance_details": False, "label_details": False}
    filters = {"global_keys": global_keys[:datarow_filter_size]}

    task_results = export_v2_test_helpers.run_dataset_export_v2_task(
        dataset, filters=filters, params=params)

    # only 2 datarows should be exported
    assert len(task_results) == datarow_filter_size
    # only filtered datarows should be exported
    assert set([dr['data_row']['global_key'] for dr in task_results
               ]) == set(global_keys[:datarow_filter_size])
