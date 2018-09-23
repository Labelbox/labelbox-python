import json
import os
import pytest
import xmltodict

import labelbox.exporters.coco_exporter as lb2co
import labelbox.exporters.voc_exporter as lb2pa


class TestCocoExporter(object):
    def test_labelbox_1(self, tmpfile, datadir):
        labeled_data = datadir.join('labelbox_1.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile)

    def test_labelbox_2(self, tmpfile, datadir):
        labeled_data = datadir.join('labelbox_2.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile)

    def test_v2(self, tmpfile, datadir):
        labeled_data = datadir.join('v2_wkt.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile)

    def test_v3(self, tmpfile, datadir):
        labeled_data = datadir.join('v3_wkt.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile)

    def test_v3_rectancle(self, tmpfile, datadir):
        labeled_data = datadir.join('v3_wkt_rectangle.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile)

    def test_xy_1(self, tmpfile, datadir):
        labeled_data = datadir.join('labelbox_xy_1.json')
        print(labeled_data)
        # lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile, label_format='XY')

    def test_v3_xy(self, tmpfile, datadir):
        labeled_data = datadir.join('v3_xy.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile, label_format='XY')

    def test_empty_skipped(self, tmpfile, datadir):
        labeled_data = datadir.join('empty_skipped.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile)

    def test_non_polygons(self, tmpfile, datadir):
        labeled_data = datadir.join('non_polygon.json')
        lb2co.from_json(labeled_data=labeled_data, coco_output=tmpfile, label_format='XY')


class TestVocExporter(object):
    def test_wkt_1(self, tmpdir, datadir):
        labeled_data = datadir.join('labelbox_1.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir)

    def test_wkt_2(self, tmpdir, datadir):
        labeled_data = datadir.join('labelbox_2.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir)

    def test_v2_wkt(self, tmpdir, datadir):
        labeled_data = datadir.join('v2_wkt.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir)

    def test_v3_wkt(self, tmpdir, datadir):
        labeled_data = datadir.join('v3_wkt.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir)

    def test_v3_wkt_bndbox(self, tmpdir, datadir):
        labeled_data = datadir.join('v3_wkt_rectangle.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir, label_format='WKT')

        with open(labeled_data, 'r') as f:
            annotation_file_path = os.path.join(tmpdir, json.load(f)[0]['ID'] + '.xml')
            with open(annotation_file_path, 'r') as f:
                annotation = xmltodict.parse(f.read())
                assert 'bndbox' in annotation['annotation']['object']

    def test_xy_1(self, tmpdir, datadir):
        labeled_data = datadir.join('labelbox_xy_1.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir, label_format='XY')

    def test_v3_xy(self, tmpdir, datadir):
        labeled_data = datadir.join('v3_xy.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir, label_format='XY')

    def test_empty_skipped(self, tmpdir, datadir):
        labeled_data = datadir.join('empty_skipped.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir, label_format='WKT')

    def test_bad_label_format(self, tmpdir, datadir):
        labeled_data = datadir.join('labelbox_xy_1.json')
        with pytest.raises(lb2pa.UnknownFormatError):
            lb2pa.from_json(labeled_data, tmpdir, tmpdir, label_format='INVALID')

    def test_non_polygons(self, tmpdir, datadir):
        labeled_data = datadir.join('non_polygon.json')
        lb2pa.from_json(labeled_data, tmpdir, tmpdir, label_format='XY')
