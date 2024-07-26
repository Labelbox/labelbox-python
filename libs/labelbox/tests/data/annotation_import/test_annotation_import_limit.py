import itertools
import uuid
from labelbox.schema.annotation_import import AnnotationImport, MALPredictionImport
from labelbox.schema.media_type import MediaType
import pytest
from unittest.mock import patch


@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 1)
def test_above_annotation_limit_on_single_import_on_single_data_row(annotations_by_media_type):

    annotations_ndjson =  list(itertools.chain.from_iterable(annotations_by_media_type[MediaType.Image]))
    data_row_id = annotations_ndjson[0]["dataRow"]["id"]

    data_row_annotations = [annotation for annotation in annotations_ndjson if annotation["dataRow"]["id"] == data_row_id and "bbox" in annotation]
    
    with pytest.raises(ValueError):
        AnnotationImport._validate_data_rows([data_row_annotations[0]]*2)


@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 1)
def test_above_annotation_limit_divided_among_different_rows(annotations_by_media_type):

    annotations_ndjson =  list(itertools.chain.from_iterable(annotations_by_media_type[MediaType.Image]))
    data_row_id = annotations_ndjson[0]["dataRow"]["id"]
    
    first_data_row_annotation = [annotation for annotation in annotations_ndjson if annotation["dataRow"]["id"] == data_row_id and "bbox" in annotation][0]
    
    second_data_row_annotation = first_data_row_annotation.copy()
    second_data_row_annotation["dataRow"]["id"] == "data_row_id_2"
    
    with pytest.raises(ValueError):
        AnnotationImport._validate_data_rows([first_data_row_annotation, second_data_row_annotation]*2)