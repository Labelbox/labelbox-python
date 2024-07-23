from labelbox.schema.media_type import MediaType
from labelbox.schema.project import Project
import pytest

from labelbox import parser
from pytest_cases import parametrize, fixture_ref

from labelbox.exceptions import MALValidationError
from labelbox.schema.bulk_import_request import (NDChecklist, NDClassification,
                                                 NDMask, NDPolygon, NDPolyline,
                                                 NDRadio, NDRectangle, NDText,
                                                 NDTextEntity, NDTool,
                                                 _validate_ndjson)
"""
- These NDlabels are apart of bulkImportReqeust and should be removed once bulk import request is removed
"""

def test_classification_construction(checklist_inference, text_inference):
    checklist = NDClassification.build(checklist_inference[0])
    assert isinstance(checklist, NDChecklist)
    text = NDClassification.build(text_inference[0])
    assert isinstance(text, NDText)


@parametrize("inference, expected_type",
             [(fixture_ref('polygon_inference'), NDPolygon),
              (fixture_ref('rectangle_inference'), NDRectangle),
              (fixture_ref('line_inference'), NDPolyline),
              (fixture_ref('entity_inference'), NDTextEntity),
              (fixture_ref('segmentation_inference'), NDMask),
              (fixture_ref('segmentation_inference_rle'), NDMask),
              (fixture_ref('segmentation_inference_png'), NDMask)])
def test_tool_construction(inference, expected_type):
    assert isinstance(NDTool.build(inference[0]), expected_type)


def no_tool(text_inference, module_project):
    pred = text_inference[0].copy()
    #Missing key
    del pred['answer']
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)

@pytest.mark.parametrize(
    "configured_project",
    [MediaType.Text],
    indirect=True
)
def test_invalid_text(text_inference, configured_project):
    #and if it is not a string
    pred = text_inference[0].copy()
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


def test_invalid_checklist_item(checklist_inference,
                                module_project):
    #Only two points
    pred = checklist_inference[0].copy()
    pred['answers'] = [pred['answers'][0], pred['answers'][0]]
    #Duplicate schema ids
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)

    pred['answers'] = [{"name": "asdfg"}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)

    pred['answers'] = [{"schemaId": "1232132132"}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)

    pred['answers'] = [{}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)

    pred['answers'] = []
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)

    del pred['answers']
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)


def test_invalid_polygon(polygon_inference, module_project):
    #Only two points
    pred = polygon_inference[0].copy()
    pred['polygon'] = [{"x": 100, "y": 100}, {"x": 200, "y": 200}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)


@pytest.mark.parametrize(
    "configured_project",
    [MediaType.Text],
    indirect=True
)
def test_incorrect_entity(entity_inference, configured_project):
    entity = entity_inference[0].copy()
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


@pytest.mark.skip("Test wont work/fails randomly since projects have to have a media type and could be missing features from prediction list")
def test_all_validate_json(module_project, predictions):
    #Predictions contains one of each type of prediction.
    #These should be properly formatted and pass.
    _validate_ndjson(predictions[0], module_project)


def test_incorrect_line(line_inference, module_project):
    line = line_inference[0].copy()
    line["line"] = [line["line"][0]]  #Just one point
    with pytest.raises(MALValidationError):
        _validate_ndjson([line], module_project)


def test_incorrect_rectangle(rectangle_inference,
                             module_project):
    del rectangle_inference[0]['bbox']['top']
    with pytest.raises(MALValidationError):
        _validate_ndjson([rectangle_inference],
                         module_project)


def test_duplicate_tools(rectangle_inference, module_project):
    pred = rectangle_inference[0].copy()
    pred['polygon'] = [{"x": 100, "y": 100}, {"x": 200, "y": 200}]
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)


def test_invalid_feature_schema(module_project,
                                rectangle_inference):
    pred = rectangle_inference[0].copy()
    pred['schemaId'] = "blahblah"
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)


def test_name_only_feature_schema(module_project,
                                  rectangle_inference):
    pred = rectangle_inference[0].copy()
    _validate_ndjson([pred], module_project)


def test_schema_id_only_feature_schema(module_project,
                                       rectangle_inference):
    pred = rectangle_inference[0].copy()
    del pred['name']
    ontology = module_project.ontology().normalized["tools"]
    for tool in ontology:
        if tool["name"] == "bbox":
            feature_schema_id = tool["featureSchemaId"]
    pred["schemaId"] = feature_schema_id
    _validate_ndjson([pred], module_project)


def test_missing_feature_schema(module_project,
                                rectangle_inference):
    pred = rectangle_inference[0].copy()
    del pred['name']
    with pytest.raises(MALValidationError):
        _validate_ndjson([pred], module_project)


def test_validate_ndjson(tmp_path, configured_project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        configured_project.upload_annotations(
            name="name", annotations=str(file_path), validate=True)


def test_validate_ndjson_uuid(tmp_path, configured_project,
                              predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions.copy()
    repeat_uuid[0]['uuid'] = 'test_uuid'
    repeat_uuid[1]['uuid'] = 'test_uuid'

    with file_path.open("w") as f:
        parser.dump(repeat_uuid, f)

    with pytest.raises(MALValidationError):
        configured_project.upload_annotations(
            name="name", validate=True, annotations=str(file_path))

    with pytest.raises(MALValidationError):
        configured_project.upload_annotations(
            name="name", validate=True, annotations=repeat_uuid)


@pytest.mark.parametrize("configured_project", [MediaType.Video], indirect=True)
def test_video_upload(video_checklist_inference,
                      configured_project):
    pred = video_checklist_inference[0].copy()
    _validate_ndjson([pred], configured_project)
