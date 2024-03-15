import pytest
from labelbox import DataRow
from labelbox.schema.identifiable import GlobalKey, UniqueId
from labelbox.schema.identifiables import GlobalKeys, UniqueIds


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

    data = [(UniqueId(data_rows[0].uid), 1, 2), (UniqueId(data_rows[1].uid), 2),
            (UniqueId(data_rows[2].uid), 3)]
    success = project.set_labeling_parameter_overrides(data)
    assert success
    updated_overrides = list(project.labeling_parameter_overrides())
    assert len(updated_overrides) == 3
    assert {o.number_of_labels for o in updated_overrides} == {1, 1, 1}
    assert {o.priority for o in updated_overrides} == {1, 2, 3}

    data = [(GlobalKey(data_rows[0].global_key), 2, 2),
            (GlobalKey(data_rows[1].global_key), 3, 3),
            (GlobalKey(data_rows[2].global_key), 4)]
    success = project.set_labeling_parameter_overrides(data)
    assert success
    updated_overrides = list(project.labeling_parameter_overrides())
    assert len(updated_overrides) == 3
    assert {o.number_of_labels for o in updated_overrides} == {1, 1, 1}
    assert {o.priority for o in updated_overrides} == {2, 3, 4}

    with pytest.raises(TypeError) as exc_info:
        data = [(data_rows[2], "a_string", 3)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
            f"Priority must be an int. Found <class 'str'> for data_row_identifier {data_rows[2].uid}"

    with pytest.raises(TypeError) as exc_info:
        data = [(data_rows[2].uid, 1)]
        project.set_labeling_parameter_overrides(data)
    assert str(exc_info.value) == \
            f"Data row identifier should be be of type DataRow, UniqueId or GlobalKey. Found <class 'str'> for data_row_identifier {data_rows[2].uid}"


def test_set_labeling_priority(consensus_project_with_batch):
    [project, _, data_rows] = consensus_project_with_batch

    init_labeling_parameter_overrides = list(
        project.labeling_parameter_overrides())
    assert len(init_labeling_parameter_overrides) == 3
    assert {o.priority for o in init_labeling_parameter_overrides} == {5, 5, 5}

    data = [data_row.uid for data_row in data_rows]
    success = project.update_data_row_labeling_priority(data, 1)
    lo = list(project.labeling_parameter_overrides())
    assert success
    assert len(lo) == 3
    assert {o.priority for o in lo} == {1, 1, 1}

    data = [data_row.uid for data_row in data_rows]
    success = project.update_data_row_labeling_priority(UniqueIds(data), 2)
    lo = list(project.labeling_parameter_overrides())
    assert success
    assert len(lo) == 3
    assert {o.priority for o in lo} == {2, 2, 2}

    data = [data_row.global_key for data_row in data_rows]
    success = project.update_data_row_labeling_priority(GlobalKeys(data), 3)
    lo = list(project.labeling_parameter_overrides())
    assert success
    assert len(lo) == 3
    assert {o.priority for o in lo} == {3, 3, 3}
