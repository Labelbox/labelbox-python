import pytest
from labelbox import DataRow


def test_labeling_parameter_overrides(consensus_project_with_batch):
    [project, _, data_rows] = consensus_project_with_batch

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


def test_set_labeling_priority(consensus_project_with_batch):
    [project, _, data_rows] = consensus_project_with_batch

    init_labeling_parameter_overrides = list(
        project.labeling_parameter_overrides())
    assert len(init_labeling_parameter_overrides) == 3
    assert {o.priority for o in init_labeling_parameter_overrides} == {5, 5, 5}

    data = [data_row.uid for data_row in data_rows]
    success = project.update_data_row_labeling_priority(data, 1)
    assert success

    updated_overrides = list(project.labeling_parameter_overrides())
    assert len(updated_overrides) == 3
    assert {o.priority for o in updated_overrides} == {1, 1, 1}
