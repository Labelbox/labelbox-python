import time
import uuid
from labelbox import parser
from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.label import Label
import pytest
from labelbox import ModelRun

from labelbox.schema.annotation_import import (
    AnnotationImportState,
    MEAPredictionImport,
)
from labelbox.data.serialization import NDJsonConverter
from labelbox.schema.export_params import ModelRunExportParams

"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""

# Every test that creates an MEA prediction import is skipped: the backend
# rejects the createModelErrorAnalysisPredictionImport mutation, which is the
# only thing ModelRun.add_predictions() and MEAPredictionImport.create*() call.
# Tests that only read a model run still work and stay enabled.
mea_prediction_import_removed = pytest.mark.skip(
    reason="MEA (Model Error Analysis) prediction import is no longer supported "
    "by the backend: the prediction import service rejects every import of "
    "that type, so ModelRun.add_predictions() fails with '9 FAILED_PRECONDITION: "
    "MEA prediction import has been deprecated' (python-monorepo #2515)."
)


@mea_prediction_import_removed
@pytest.mark.order(1)
def test_create_from_objects(
    model_run_with_data_rows,
    object_predictions_for_annotation_import,
    annotation_import_test_helpers,
):
    name = str(uuid.uuid4())
    object_predictions = object_predictions_for_annotation_import
    use_data_row_ids = [p["dataRow"]["id"] for p in object_predictions]
    model_run_with_data_rows.upsert_data_rows(use_data_row_ids)

    annotation_import = model_run_with_data_rows.add_predictions(
        name=name, predictions=object_predictions
    )

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, object_predictions
    )
    annotation_import.wait_until_done()

    assert annotation_import.state == AnnotationImportState.FINISHED
    annotation_import_test_helpers.download_and_assert_status(
        annotation_import.status_file_url
    )


@mea_prediction_import_removed
def test_create_from_objects_global_key(
    client,
    model_run_with_data_rows,
    polygon_inference,
    annotation_import_test_helpers,
):
    name = str(uuid.uuid4())
    dr = client.get_data_row(polygon_inference[0]["dataRow"]["id"])
    polygon_inference[0]["dataRow"]["globalKey"] = dr.global_key
    del polygon_inference[0]["dataRow"]["id"]
    object_predictions = [polygon_inference[0]]

    annotation_import = model_run_with_data_rows.add_predictions(
        name=name, predictions=object_predictions
    )

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, object_predictions
    )
    annotation_import.wait_until_done()

    assert annotation_import.state == AnnotationImportState.FINISHED
    annotation_import_test_helpers.download_and_assert_status(
        annotation_import.status_file_url
    )


@mea_prediction_import_removed
def test_create_from_objects_with_confidence(
    predictions_with_confidence,
    model_run_with_data_rows,
    annotation_import_test_helpers,
):
    name = str(uuid.uuid4())

    object_prediction_data_rows = set(
        [
            object_prediction["dataRow"]["id"]
            for object_prediction in predictions_with_confidence
        ]
    )
    # MUST have all data rows in the model run
    model_run_with_data_rows.upsert_data_rows(
        data_row_ids=list(object_prediction_data_rows)
    )

    annotation_import = model_run_with_data_rows.add_predictions(
        name=name, predictions=predictions_with_confidence
    )

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, predictions_with_confidence
    )
    annotation_import.wait_until_done()

    assert annotation_import.state == AnnotationImportState.FINISHED
    annotation_import_test_helpers.download_and_assert_status(
        annotation_import.status_file_url
    )


@mea_prediction_import_removed
def test_create_from_objects_all_project_labels(
    model_run_with_all_project_labels,
    object_predictions_for_annotation_import,
    annotation_import_test_helpers,
):
    name = str(uuid.uuid4())
    object_predictions = object_predictions_for_annotation_import
    use_data_row_ids = [p["dataRow"]["id"] for p in object_predictions]
    model_run_with_all_project_labels.upsert_data_rows(use_data_row_ids)

    annotation_import = model_run_with_all_project_labels.add_predictions(
        name=name, predictions=object_predictions
    )

    assert (
        annotation_import.model_run_id == model_run_with_all_project_labels.uid
    )
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, object_predictions
    )
    annotation_import.wait_until_done()

    assert annotation_import.state == AnnotationImportState.FINISHED
    annotation_import_test_helpers.download_and_assert_status(
        annotation_import.status_file_url
    )


def _export_model_run_labels(
    model_run: ModelRun, expected_data_row_count: int, timeout_seconds=180
):
    """The first label of each data row of a model run, once the export has them.

    `upsert_labels` returns when the labels are attached to the model run, and
    the export catches up a little later: until then a data row comes out with
    no label for the run. So export again while any is missing, and fail if
    they have not all arrived in time.
    """
    deadline = time.time() + timeout_seconds
    while True:
        export_task = model_run.export()
        export_task.wait_till_done()
        labels_by_data_row = [
            (
                data_row.json["data_row"]["id"],
                data_row.json["experiments"][model_run.model_id]["runs"][
                    model_run.uid
                ]["labels"],
            )
            for data_row in export_task.get_buffered_stream()
        ]
        if len(labels_by_data_row) >= expected_data_row_count and all(
            labels for _, labels in labels_by_data_row
        ):
            return [
                (data_row_id, labels[0])
                for data_row_id, labels in labels_by_data_row
            ]

        missing = [
            data_row_id
            for data_row_id, labels in labels_by_data_row
            if not labels
        ]
        assert time.time() < deadline, (
            f"After {timeout_seconds}s the export of model run {model_run.uid} "
            f"had {len(labels_by_data_row)} of {expected_data_row_count} data "
            f"rows, {len(missing)} of them without a label"
        )
        time.sleep(5)


def test_model_run_project_labels(
    model_run_with_all_project_labels: ModelRun, model_run_predictions
):
    model_run = model_run_with_all_project_labels
    expected_data_row_count = len(
        set(prediction["dataRow"]["id"] for prediction in model_run_predictions)
    )

    # exports to list of tuples (data_row_id, label) needed to adapt test to export v2 instead of export v1 since data rows ids are not at label level in export v2.
    model_run_exported_labels = _export_model_run_labels(
        model_run, expected_data_row_count
    )

    labels_indexed_by_name = {}

    # making sure the labels are in this model run are all labels uploaded to the project
    # by comparing some 'immutable' attributes
    # multiple data rows per prediction import
    for data_row_id, label in model_run_exported_labels:
        for object in label["annotations"]["objects"]:
            name = object["name"]
            labels_indexed_by_name[f"{name}-{data_row_id}"] = {
                "label": label,
                "data_row_id": data_row_id,
            }

    assert (len(labels_indexed_by_name.keys())) == len(
        [prediction["dataRow"]["id"] for prediction in model_run_predictions]
    )

    expected_data_row_ids = set(
        [prediction["dataRow"]["id"] for prediction in model_run_predictions]
    )
    expected_objects = set(
        [prediction["name"] for prediction in model_run_predictions]
    )
    for data_row_id, actual_label in model_run_exported_labels:
        assert data_row_id in expected_data_row_ids
        assert len(expected_objects) == len(
            actual_label["annotations"]["objects"]
        )


@mea_prediction_import_removed
def test_create_from_label_objects(
    model_run_with_data_rows,
    object_predictions_for_annotation_import,
    annotation_import_test_helpers,
):
    name = str(uuid.uuid4())
    use_data_row_id = [
        p["dataRow"]["id"] for p in object_predictions_for_annotation_import
    ]

    model_run_with_data_rows.upsert_data_rows(use_data_row_id)

    predictions = []
    for data_row_id in use_data_row_id:
        predictions.append(
            Label(
                data=GenericDataRowData(
                    uid=data_row_id,
                ),
                annotations=[
                    ObjectAnnotation(
                        name="polygon",
                        value=Polygon(
                            points=[
                                Point(x=147.692, y=118.154),
                                Point(x=142.769, y=104.923),
                                Point(x=57.846, y=118.769),
                                Point(x=28.308, y=169.846),
                                Point(x=147.692, y=118.154),
                            ],
                        ),
                    ),
                    ObjectAnnotation(
                        name="bbox",
                        value=Rectangle(
                            start=Point(x=58.0, y=48.0),
                            end=Point(x=70.0, y=113.0),
                        ),
                    ),
                    ObjectAnnotation(
                        name="polyline",
                        value=Line(
                            points=[
                                Point(x=147.692, y=118.154),
                                Point(x=150.692, y=160.154),
                            ],
                        ),
                    ),
                ],
            ),
        )

    annotation_import = model_run_with_data_rows.add_predictions(
        name=name, predictions=predictions
    )

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    normalized_predictions = NDJsonConverter.serialize(predictions)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, normalized_predictions
    )
    annotation_import.wait_until_done()

    assert annotation_import.state == AnnotationImportState.FINISHED
    annotation_import_test_helpers.download_and_assert_status(
        annotation_import.status_file_url
    )


@mea_prediction_import_removed
def test_create_from_local_file(
    tmp_path,
    model_run_with_data_rows,
    object_predictions_for_annotation_import,
    annotation_import_test_helpers,
):
    use_data_row_ids = [
        p["dataRow"]["id"] for p in object_predictions_for_annotation_import
    ]
    model_run_with_data_rows.upsert_data_rows(use_data_row_ids)

    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        parser.dump(object_predictions_for_annotation_import, f)

    annotation_import = model_run_with_data_rows.add_predictions(
        name=name, predictions=str(file_path)
    )

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url,
        object_predictions_for_annotation_import,
    )
    annotation_import.wait_until_done()

    assert annotation_import.state == AnnotationImportState.FINISHED
    annotation_import_test_helpers.download_and_assert_status(
        annotation_import.status_file_url
    )


@mea_prediction_import_removed
def test_predictions_with_custom_metrics(
    model_run,
    object_predictions_for_annotation_import,
    annotation_import_test_helpers,
):
    name = str(uuid.uuid4())
    object_predictions = object_predictions_for_annotation_import
    use_data_row_ids = [p["dataRow"]["id"] for p in object_predictions]
    model_run.upsert_data_rows(use_data_row_ids)

    annotation_import = model_run.add_predictions(
        name=name, predictions=object_predictions
    )

    assert annotation_import.model_run_id == model_run.uid
    annotation_import.wait_until_done()
    assert annotation_import.state == AnnotationImportState.FINISHED

    task = model_run.export_v2(params=ModelRunExportParams(predictions=True))
    task.wait_till_done()

    assert annotation_import.state == AnnotationImportState.FINISHED
    annotation_import_test_helpers.download_and_assert_status(
        annotation_import.status_file_url
    )


@mea_prediction_import_removed
def test_get(client, model_run_with_data_rows, annotation_import_test_helpers):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    model_run_with_data_rows.add_predictions(name=name, predictions=url)

    annotation_import = MEAPredictionImport.from_name(
        client, model_run_id=model_run_with_data_rows.uid, name=name
    )

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import_test_helpers.check_running_state(
        annotation_import, name, url
    )
    annotation_import.wait_until_done()


@mea_prediction_import_removed
@pytest.mark.slow
def test_wait_till_done(model_run_predictions, model_run_with_data_rows):
    name = str(uuid.uuid4())
    annotation_import = model_run_with_data_rows.add_predictions(
        name=name, predictions=model_run_predictions
    )

    assert len(annotation_import.inputs) == len(model_run_predictions)
    annotation_import.wait_until_done()
    assert annotation_import.state == AnnotationImportState.FINISHED
    # Check that the status files are being returned as expected
    assert len(annotation_import.errors) == 0
    assert len(annotation_import.inputs) == len(model_run_predictions)
    input_uuids = [
        input_annot["uuid"] for input_annot in annotation_import.inputs
    ]
    inference_uuids = [pred["uuid"] for pred in model_run_predictions]
    assert set(input_uuids) == set(inference_uuids)
    assert len(annotation_import.statuses) == len(model_run_predictions)
    for status in annotation_import.statuses:
        assert status["status"] == "SUCCESS"
    status_uuids = [
        input_annot["uuid"] for input_annot in annotation_import.statuses
    ]
    assert set(input_uuids) == set(status_uuids)
