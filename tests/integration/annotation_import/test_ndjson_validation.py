import pytest

from labelbox import parser
from pytest_cases import parametrize, fixture_ref

from labelbox.exceptions import MALValidationError
from labelbox.schema.bulk_import_request import (NDChecklist, NDClassification,
                                                 NDMask, NDPolygon, NDPolyline,
                                                 NDRadio, NDRectangle, NDText,
                                                 NDTextEntity, NDTool,
                                                 _validate_ndjson)


def test_classification_construction(checklist_inference, text_inference):
    checklist = NDClassification.build(checklist_inference)
    assert isinstance(checklist, NDChecklist)
    text = NDClassification.build(text_inference)
    assert isinstance(text, NDText)


def test_subclassification_construction(rectangle_inference):
    tool = NDTool.build(rectangle_inference)
    assert len(tool.classifications) == 1, "Subclass was not constructed"
    assert isinstance(tool.classifications[0], NDRadio)


@parametrize("inference, expected_type",
             [(fixture_ref('polygon_inference'), NDPolygon),
              (fixture_ref('rectangle_inference'), NDRectangle),
              (fixture_ref('line_inference'), NDPolyline),
              (fixture_ref('entity_inference'), NDTextEntity),
              (fixture_ref('segmentation_inference'), NDMask),
              (fixture_ref('segmentation_inference_rle'), NDMask),
              (fixture_ref('segmentation_inference_png'), NDMask)])
def test_tool_construction(inference, expected_type):
    assert isinstance(NDTool.build(inference), expected_type)


def test_incorrect_feature_schema(rectangle_inference, polygon_inference,
                                  configured_project):
    #Valid but incorrect feature schema
    #Prob the error message says something about the config not anything useful. We might want to fix this.
    pred = rectangle_inference.copy()
    pred['schemaId'] = polygon_inference['schemaId']
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def no_tool(text_inference, configured_project):
    pred = text_inference.copy()
    #Missing key
    del pred['answer']
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def test_invalid_text(text_inference, configured_project):
    #and if it is not a string
    pred = text_inference.copy()
    #Extra and wrong key
    del pred['answer']
    pred['answers'] = []
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)
    del pred['answers']

    #Invalid type
    pred['answer'] = []
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)

    #Invalid type
    pred['answer'] = None
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def test_invalid_checklist_item(checklist_inference, configured_project):
    #Only two points
    pred = checklist_inference.copy()
    pred['answers'] = [pred['answers'][0], pred['answers'][0]]
    #Duplicate schema ids
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)

    pred['answers'] = [{"name": "asdfg"}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)

    pred['answers'] = [{"schemaId": "1232132132"}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)

    pred['answers'] = [{}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)

    pred['answers'] = []
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)

    del pred['answers']
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def test_invalid_polygon(polygon_inference, configured_project):
    #Only two points
    pred = polygon_inference.copy()
    pred['polygon'] = [{"x": 100, "y": 100}, {"x": 200, "y": 200}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def test_incorrect_entity(entity_inference, configured_project):
    entity = entity_inference.copy()
    #Location cannot be a list
    entity["location"] = [0, 10]
    with pytest.raises(MALValidationError):
        _validate_ndjson([entity], configured_project)

    entity["location"] = {"start": -1, "end": 5}
    with pytest.raises(MALValidationError):
        _validate_ndjson([entity], configured_project)

    entity["location"] = {"start": 15, "end": 5}
    with pytest.raises(MALValidationError):
        _validate_ndjson([entity], configured_project)


def test_incorrect_mask(segmentation_inference, configured_project):
    seg = segmentation_inference.copy()
    seg['mask']['colorRGB'] = [-1, 0, 10]
    with pytest.raises(MALValidationError):
        _validate_ndjson([seg], configured_project)

    seg['mask']['colorRGB'] = [0, 0]
    with pytest.raises(MALValidationError):
        _validate_ndjson([seg], configured_project)

    seg['mask'] = {'counts': [0], 'size': [0, 1]}
    with pytest.raises(MALValidationError):
        _validate_ndjson([seg], configured_project)

    seg['mask'] = {'counts': [-1], 'size': [1, 1]}
    with pytest.raises(MALValidationError):
        _validate_ndjson([seg], configured_project)


def test_all_validate_json(configured_project, predictions):
    #Predictions contains one of each type of prediction.
    #These should be properly formatted and pass.
    _validate_ndjson(predictions, configured_project)


def test_incorrect_line(line_inference, configured_project):
    line = line_inference.copy()
    line["line"] = [line["line"][0]]  #Just one point
    with pytest.raises(MALValidationError):
        _validate_ndjson([line], configured_project)


def test_incorrect_rectangle(rectangle_inference, configured_project):
    del rectangle_inference['bbox']['top']
    with pytest.raises(MALValidationError):
        _validate_ndjson([rectangle_inference], configured_project)


def test_duplicate_tools(rectangle_inference, configured_project):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    pred['polygon'] = [{"x": 100, "y": 100}, {"x": 200, "y": 200}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def test_invalid_feature_schema(configured_project, rectangle_inference):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    pred['schemaId'] = "blahblah"
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def test_name_only_feature_schema(configured_project, rectangle_inference):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    del pred['schemaId']
    _validate_ndjson([pred], configured_project)


def test_schema_id_only_feature_schema(configured_project, rectangle_inference):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    del pred['name']
    _validate_ndjson([pred], configured_project)


def test_missing_feature_schema(configured_project, rectangle_inference):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    del pred['schemaId']
    del pred['name']
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], configured_project)


def test_validate_ndjson(tmp_path, configured_project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        configured_project.upload_annotations(name="name",
                                              annotations=str(file_path),
                                              validate=True)


def test_validate_ndjson_uuid(tmp_path, configured_project, predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions.copy()
    repeat_uuid[0]['uuid'] = 'test_uuid'
    repeat_uuid[1]['uuid'] = 'test_uuid'

    with file_path.open("w") as f:
        parser.dump(repeat_uuid, f)

    with pytest.raises(MALValidationError):
        configured_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=str(file_path))

    with pytest.raises(MALValidationError):
        configured_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=repeat_uuid)


def test_video_upload(video_checklist_inference, configured_project):
    pred = video_checklist_inference.copy()
    _validate_ndjson([pred], configured_project)
