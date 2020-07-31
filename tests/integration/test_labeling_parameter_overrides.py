from labelbox import DataRow

IMG_URL = "https://picsum.photos/200/300"


def test_labeling_parameter_overrides(project, rand_gen):
    dataset = project.client.create_dataset(name=rand_gen(str),
                                            projects=project)

    task = dataset.create_data_rows([{DataRow.row_data: IMG_URL}] * 20)
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

    success = project.unset_labeling_parameter_overrides(
        [data[0][0], data[1][0]])
    assert success

    # TODO ensure that the labeling parameter overrides are removed
    # currently this doesn't work so the count remains 3
    assert len(list(project.labeling_parameter_overrides())) == 1

    dataset.delete()
