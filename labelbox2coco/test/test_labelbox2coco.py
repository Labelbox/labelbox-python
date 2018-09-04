import os
import pytest
import tempfile

import labelbox2coco as lb2co


@pytest.fixture
def output_file():
    with tempfile.NamedTemporaryFile() as f:
        yield f.name


def test_labelbox_1(output_file):
    labeled_data = os.path.abspath('test-fixtures/labelbox_1.json')
    lb2co.from_json(labeled_data=labeled_data, coco_output=output_file)

def test_labelbox_2(output_file):
    labeled_data = os.path.abspath('test-fixtures/labelbox_2.json')
    lb2co.from_json(labeled_data=labeled_data, coco_output=output_file)

def test_v2(output_file):
    labeled_data = os.path.abspath('test-fixtures/v2_wkt.json')
    lb2co.from_json(labeled_data=labeled_data, coco_output=output_file)

def test_v3(output_file):
    labeled_data = os.path.abspath('test-fixtures/v3_wkt.json')
    lb2co.from_json(labeled_data=labeled_data, coco_output=output_file)

def test_v3_rectancle(output_file):
    labeled_data = os.path.abspath('test-fixtures/v3_wkt_rectangle.json')
    lb2co.from_json(labeled_data=labeled_data, coco_output=output_file)

def test_empty_skipped(output_file):
    labeled_data = os.path.abspath('test-fixtures/empty_skipped.json')
    lb2co.from_json(labeled_data=labeled_data, coco_output=output_file)
