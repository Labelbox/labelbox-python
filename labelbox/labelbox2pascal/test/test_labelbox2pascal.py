import json
import shutil
import tempfile

import labelbox2pascal as lb2pa
import pytest
import xmltodict

@pytest.fixture
def output_dir():
    output_directory = tempfile.mkdtemp()
    yield output_directory
    shutil.rmtree(output_directory)

def test_wkt_1(output_dir):
    lb2pa.from_json('test-fixtures/labelbox_1.json', output_dir, output_dir)

def test_wkt_2(output_dir):
    lb2pa.from_json('test-fixtures/labelbox_2.json', output_dir, output_dir)

def test_v2_wkt(output_dir):
    lb2pa.from_json('test-fixtures/v2_wkt.json', output_dir, output_dir)

def test_v3_wkt(output_dir):
    lb2pa.from_json('test-fixtures/v3_wkt.json', output_dir, output_dir)

def test_v3_wkt_bndbox(output_dir):
    fixture = 'test-fixtures/v3_wkt_rectangle.json'
    with open(fixture, 'r') as f:
        annotation_file_path = output_dir + '/' + json.load(f)[0]['ID'] + '.xml'

    lb2pa.from_json(fixture, output_dir, output_dir, label_format='WKT')

    with open(annotation_file_path, 'r') as f:
        annotation = xmltodict.parse(f.read())
        assert 'bndbox' in annotation['annotation']['object']

def test_xy_1(output_dir):
    lb2pa.from_json('test-fixtures/labelbox_xy_1.json', output_dir, output_dir, label_format='XY')

def test_v3_xy(output_dir):
    lb2pa.from_json('test-fixtures/v3_xy.json', output_dir, output_dir, label_format='XY')

def test_empty_skipped(output_dir):
    lb2pa.from_json('test-fixtures/empty_skipped.json', output_dir, output_dir, label_format='WKT')

def test_bad_label_format(output_dir):
    with pytest.raises(lb2pa.UnknownFormatError):
        lb2pa.from_json('test-fixtures/labelbox_xy_1.json', output_dir, output_dir, label_format='INVALID')
