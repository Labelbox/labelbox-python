from labelbox.exceptions import UuidError
from labelbox.schema.bulk_import_request import _validate_ndjson
import pytest
import ndjson

def test_incorrect_feature_schema(rectangle_inference, polygon_inference, configured_project):
    #Valid but incorrect feature schema
    #Prob the error message says something about the config not anything useful. We might want to fix this.
    pred =  rectangle_inference.copy()
    pred['schemaId'] = polygon_inference['schemaId']
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

def no_tool(text_inference, configured_project):
    pred = text_inference.copy()
    #Missing key
    del pred['answer'] 
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

def test_invalid_datarow_id(text_inference, configured_project):
    pred = text_inference.copy()
    pred['dataRow']['id'] = "1232132131232"
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

def test_invalid_text(text_inference, configured_project):
    #and if it is not a string
    pred = text_inference.copy()
    #Extra and wrong key
    del pred['answer']
    pred['answers'] = []
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)
    del pred['answers']

    #Invalid type
    pred['answer'] = [] 
    with pytest.raises(TypeError):
        _validate_ndjson([pred], configured_project)

    #Invalid type
    pred['answer'] = None
    with pytest.raises(TypeError):
        _validate_ndjson([pred], configured_project)

def test_invalid_checklist_item(checklist_inference, configured_project):
    #Only two points
    pred = checklist_inference.copy()
    pred['answers'] = [pred['answers'][0],pred['answers'][0]]
    #Duplicate schema ids
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

    pred['answers'] = [{"schemaId" : "1232132132"}]
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

    pred['answers'] = [{}]
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

    pred['answers'] = []
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

    del pred['answers']
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)
    

def test_invalid_polygon(polygon_inference, configured_project):
    #Only two points
    pred = polygon_inference.copy()
    pred['polygon'] = [{"x" : 100, "y" : 100}, {"x" : 200, "y" : 200}]
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

    
def test_incorrect_entity(entity_inference, configured_project):
    entity = entity_inference.copy()
    entity["location"] = [0,10]
    with pytest.raises(ValueError):
        _validate_ndjson([entity], configured_project)

    entity["location"] = {"start" : -1, "end" : 5}
    with pytest.raises(ValueError):
        _validate_ndjson([entity], configured_project)

    entity["location"] = {"start" : 15, "end" : 5}
    with pytest.raises(ValueError):
        _validate_ndjson([entity], configured_project)

def test_incorrect_mask(segmentation_inference, configured_project):
    seg = segmentation_inference.copy()
    seg['mask']['colorRGB'] = [-1,0,10]
    with pytest.raises(ValueError):
        _validate_ndjson([seg], configured_project)

    seg['mask']['colorRGB'] = [0,0,0]        
    seg['mask']['instanceURI'] = 1 
    with pytest.raises(ValueError):
        _validate_ndjson([seg], configured_project)

def test_all_validate_json(configured_project, predictions):
    #Predictions contains one of each type of prediction.
    #These should be properly formatted and pass.
    _validate_ndjson(predictions, configured_project)

def test_incorrect_line(line_inference, configured_project):
    line = line_inference.copy()
    line["line"] = [line["line"][0]] #Just one point
    with pytest.raises(ValueError):
        _validate_ndjson([line], configured_project)


def test_incorrect_rectangle(rectangle_inference, configured_project):
    del rectangle_inference['bbox']['top']
    with pytest.raises(ValueError):
        _validate_ndjson([rectangle_inference], configured_project)

def test_duplicate_tools(rectangle_inference, configured_project):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    pred['polygon'] = [{"x" : 100, "y" : 100}, {"x" : 200, "y" : 200}]
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

def test_invalid_feature_schema(configured_project, rectangle_inference):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    pred['schemaId'] = "blahblah"
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)

def test_missing_feature_schema(configured_project, rectangle_inference):
    #Trying to upload a polygon and rectangle at the same time
    pred = rectangle_inference.copy()
    del pred['schemaId']
    with pytest.raises(ValueError):
        _validate_ndjson([pred], configured_project)


def test_validate_ndjson(tmp_path, configured_project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        configured_project.upload_annotations(name="name", annotations=str(file_path))


def test_validate_ndjson_uuid(tmp_path, configured_project, predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions.copy()
    repeat_uuid[0]['uuid'] = 'test_uuid'
    repeat_uuid[1]['uuid'] = 'test_uuid'

    with file_path.open("w") as f:
        ndjson.dump(repeat_uuid, f)

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name", annotations=str(file_path))

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name", annotations=repeat_uuid)

