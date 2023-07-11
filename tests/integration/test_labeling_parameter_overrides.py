import pytest
from labelbox import DataRow


def test_labeling_parameter_overrides(consensus_project, initial_dataset,
                                      rand_gen, image_url):
    project = consensus_project
    dataset = initial_dataset

    task = dataset.create_data_rows([{DataRow.row_data: image_url}] * 3)
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 3

    project.create_batch(
        rand_gen(str),
        data_rows,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )

    init_labeling_parameter_overrides = list(
        project.labeling_parameter_overrides())
    assert len(init_labeling_parameter_overrides) == 3
    assert {o.number_of_labels for o in init_labeling_parameter_overrides
           } == {1, 1, 1}
    assert {o.priority for o in init_labeling_parameter_overrides} == {5, 5, 5}
    assert {o.data_row().uid for o in init_labeling_parameter_overrides
           } == {data_rows[0].uid, data_rows[1].uid, data_rows[2].uid}

    data = [(data_rows[0], 4, 2), (data_rows[1], 3)]
    success = project.set_labeling_parameter_overrides(data)
    assert success

    updated_overrides = list(project.labeling_parameter_overrides())
    assert len(updated_overrides) == 3
    assert {o.number_of_labels for o in updated_overrides} == {1, 1, 1}
    assert {o.priority for o in updated_overrides} == {4, 3, 5}

    for override in updated_overrides:
        assert isinstance(override.data_row(), DataRow)

    success = project.unset_labeling_parameter_overrides(
        [data[0][0], data[1][0]])
    assert success

    # TODO ensure that the labeling parameter overrides are removed
    # currently this doesn't work so the count remains 3
    assert len(list(project.labeling_parameter_overrides())) == 1

    with pytest.raises(TypeError) as exc_info:
        data = [(data_rows[2], "a_string", 3)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        f"Priority must be an int. Found <class 'str'> for data_row {data_rows[2]}. Index: 0"

    with pytest.raises(TypeError) as exc_info:
        data = [(data_rows[2].uid, 1)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        "data_row should be be of type DataRow. Found <class 'str'>. Index: 0"

    with pytest.raises(ValueError) as exc_info:
        data = [(data_rows[2], 0)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
        f"Priority must be greater than 0 for data_row {data_rows[2]}. Index: 0"

    dataset.delete()
