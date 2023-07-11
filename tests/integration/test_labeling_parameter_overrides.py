import pytest
from labelbox import DataRow


def test_labeling_parameter_overrides(consensus_project, initial_dataset,
                                      rand_gen, image_url):
    project = consensus_project
    dataset = initial_dataset

    task = dataset.create_data_rows([{DataRow.row_data: image_url}] * 20)
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 20

    assert len(list(project.labeling_parameter_overrides())) == 0

    data = [(data_rows[12], 4, 3), (data_rows[3], 3, 2), (data_rows[8], 8, 5)]
    success = project.set_labeling_parameter_overrides(data)
    assert success

    overrides = list(project.labeling_parameter_overrides())
    assert len(overrides) == 3
    assert {o.number_of_labels for o in overrides} == {3, 2, 5}
    assert {o.priority for o in overrides} == {4, 3, 8}

    for override in overrides:
        assert isinstance(override.data_row(), DataRow)

    success = project.unset_labeling_parameter_overrides(
        [data[0][0], data[1][0]])
    assert success

    # TODO ensure that the labeling parameter overrides are removed
    # currently this doesn't work so the count remains 3
    assert len(list(project.labeling_parameter_overrides())) == 1

    with pytest.raises(TypeError) as exc_info:
        data = [(data_rows[12], "a_string", 3)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        f"Priority must be an int. Found <class 'str'> for data_row {data_rows[12]}. Index: 0"

    with pytest.raises(TypeError) as exc_info:
        data = [(data_rows[12], 3, "a_string")]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        f"Number of labels must be an int. Found <class 'str'> for data_row {data_rows[12]}. Index: 0"

    with pytest.raises(TypeError) as exc_info:
        data = [(data_rows[12].uid, 1, 3)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        "data_row should be be of type DataRow. Found <class 'str'>. Index: 0"

    with pytest.raises(ValueError) as exc_info:
        data = [(data_rows[12], 0, 3)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        f"Priority must be greater than 0 for data_row {data_rows[12]}. Index: 0"

    with pytest.raises(ValueError) as exc_info:
        data = [(data_rows[12], 1, 0)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        f"Number of labels must be greater than 0 for data_row {data_rows[12]}. Index: 0"

    dataset.delete()
