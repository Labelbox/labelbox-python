#
# This was commented out, as it is almost ready to go, however we do not yet have an updated
# implementation of project.upload_annotations that uses AnnotationImports rather than
# BulkImportRequest. Once we have that, we should be calling this new implementation
# rather than the old one.
# 
# 
# 
# 
# 
# 
#  import uuid
# import ndjson
# import pytest
# import requests

# from labelbox.exceptions import MALValidationError, UuidError
# from labelbox.schema.enums import AnnotationImportState
# from labelbox.schema.annotation_import import MALPredictionImport

# """
# - Here we only want to check that the uploads are calling the validation
# - Then with unit tests we can check the types of errors raised

# """


# def test_create_from_url(configured_project):
#     name = str(uuid.uuid4())
#     url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

#     annotation_import = configured_project.upload_annotations(
#         name=name, annotations=predictions)

#     assert annotation_import.project() == configured_project
#     assert annotation_import.name == name
#     assert annotation_import.input_file_url == url
#     assert annotation_import.error_file_url is None
#     assert annotation_import.status_file_url is None
#     assert annotation_import.state == AnnotationImportState.RUNNING


# def test_validate_file(client, configured_project):
#     name = str(uuid.uuid4())
#     url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
#     with pytest.raises(MALValidationError):
#         configured_project.upload_annotations(name=name,
#                                               annotations=url,
#                                               validate=True)
#         #Schema ids shouldn't match


# def test_create_from_objects(configured_project, predictions):
#     name = str(uuid.uuid4())

#     annotation_import = configured_project.upload_annotations(
#         name=name, annotations=predictions)

#     assert annotation_import.project() == configured_project
#     assert annotation_import.name == name
#     assert annotation_import.error_file_url is None
#     assert annotation_import.status_file_url is None
#     assert annotation_import.state == AnnotationImportState.RUNNING
#     assert_file_content(annotation_import.input_file_url, predictions)


# def test_create_from_local_file(tmp_path, predictions, configured_project):
#     name = str(uuid.uuid4())
#     file_name = f"{name}.ndjson"
#     file_path = tmp_path / file_name
#     with file_path.open("w") as f:
#         ndjson.dump(predictions, f)

#     annotation_import = configured_project.upload_annotations(
#         name=name, annotations=str(file_path), validate=False)

#     assert annotation_import.project() == configured_project
#     assert annotation_import.name == name
#     assert annotation_import.error_file_url is None
#     assert annotation_import.status_file_url is None
#     assert annotation_import.state == AnnotationImportState.RUNNING
#     assert_file_content(annotation_import.input_file_url, predictions)


# def test_get(client, configured_project):
#     name = str(uuid.uuid4())
#     url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
#     configured_project.upload_annotations(name=name,
#                                           annotations=url,
#                                           validate=False)

#     annotation_import = MALPredictionImport.from_name(
#         client, project_id=configured_project.uid, name=name)
#     print("asdf:", annotation_import)

#     assert annotation_import.project() == configured_project
#     assert annotation_import.name == name
#     assert annotation_import.input_file_url == url
#     assert annotation_import.error_file_url is None
#     assert annotation_import.status_file_url is None
#     assert annotation_import.state == AnnotationImportState.RUNNING


# def test_validate_ndjson(tmp_path, configured_project):
#     file_name = f"broken.ndjson"
#     file_path = tmp_path / file_name
#     with file_path.open("w") as f:
#         f.write("test")

#     with pytest.raises(ValueError):
#         configured_project.upload_annotations(name="name",
#                                               annotations=str(file_path))


# def test_validate_ndjson_uuid(tmp_path, configured_project, predictions):
#     file_name = f"repeat_uuid.ndjson"
#     file_path = tmp_path / file_name
#     repeat_uuid = predictions.copy()
#     uid = str(uuid.uuid4())
#     repeat_uuid[0]['uuid'] = uid
#     repeat_uuid[1]['uuid'] = uid

#     with file_path.open("w") as f:
#         ndjson.dump(repeat_uuid, f)

#     with pytest.raises(UuidError):
#         configured_project.upload_annotations(name="name",
#                                               annotations=str(file_path))

#     with pytest.raises(UuidError):
#         configured_project.upload_annotations(name="name",
#                                               annotations=repeat_uuid)


# @pytest.mark.slow
# def test_wait_till_done(rectangle_inference, configured_project):
#     name = str(uuid.uuid4())
#     url = configured_project.client.upload_data(content=ndjson.dumps(
#         [rectangle_inference]),
#                                                 sign=True)
#     annotation_import = configured_project.upload_annotations(name=name,
#                                                                 annotations=url,
#                                                                 validate=False)

#     assert len(annotation_import.inputs) == 1
#     annotation_import.wait_until_done()
#     assert annotation_import.state == AnnotationImportState.FINISHED

#     # Check that the status files are being returned as expected
#     assert len(annotation_import.errors) == 0
#     assert len(annotation_import.inputs) == 1
#     assert annotation_import.inputs[0]['uuid'] == rectangle_inference['uuid']
#     assert len(annotation_import.statuses) == 1
#     assert annotation_import.statuses[0]['status'] == 'SUCCESS'
#     assert annotation_import.statuses[0]['uuid'] == rectangle_inference[
#         'uuid']


# def assert_file_content(url: str, predictions):
#     response = requests.get(url)
#     assert response.text == ndjson.dumps(predictions)
