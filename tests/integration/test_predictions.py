def test_prediction_model(project, rand_gen):
    model_name = rand_gen(str)
    version = 42
    model_1 = project.create_prediction_model(model_name, version)
    assert model_1.name == model_name
    assert model_1.version == version
    assert project.active_prediction_model() == model_1

    model_2 = project.create_prediction_model(rand_gen(str), 22)
    assert project.active_prediction_model() == model_2


def test_predictions(label_pack, rand_gen):
    project, dataset, data_row, label = label_pack
    model_1 = project.create_prediction_model(rand_gen(str), 12)

    assert set(project.predictions()) == set()
    pred_1 = project.create_prediction("l1", data_row)
    assert pred_1.label == "l1"
    assert set(model_1.created_predictions()) == {pred_1}
    assert set(project.predictions()) == {pred_1}
    assert set(data_row.predictions()) == {pred_1}
    assert pred_1.prediction_model() == model_1
    assert pred_1.data_row() == data_row
    assert pred_1.project() == project
    label_2 = project.create_label(data_row=data_row,
                                   label="test",
                                   seconds_to_label=0.0)

    model_2 = project.create_prediction_model(rand_gen(str), 12)
    assert set(project.predictions()) == {pred_1}
    pred_2 = project.create_prediction("l2", data_row)
    assert pred_2.label == "l2"
    assert set(model_1.created_predictions()) == {pred_1}
    assert set(model_2.created_predictions()) == {pred_2}
    assert set(project.predictions()) == {pred_1, pred_2}
    assert set(data_row.predictions()) == {pred_1, pred_2}
