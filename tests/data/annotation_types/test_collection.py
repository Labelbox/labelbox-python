from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest
from labelbox import DataRow
from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.data.annotation_types.collection import (LabelCollection,
                                                       LabelGenerator)
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.label import Label
from labelbox.schema.ontology import OntologyBuilder, Tool


@pytest.fixture
def list_of_labels():
    return [Label(data=RasterData(url="http://someurl")) for _ in range(5)]


@pytest.fixture
def signer():

    def get_signer(uuid):
        return lambda x: uuid

    return get_signer


class FakeDataset:

    def __init__(self):
        self.uid = "ckrb4tgm51xl10ybc7lv9ghm7"
        self.exports = []

    def create_data_row(self, row_data, external_id=None):
        if external_id is None:
            external_id = "an external_id"
        return SimpleNamespace(uid=self.uid, external_id=external_id)

    def create_data_rows(self, args):
        for arg in args:
            self.exports.append(
                SimpleNamespace(row_data=arg[DataRow.row_data],
                                external_id=arg[DataRow.external_id],
                                uid=self.uid))
        return self

    def wait_til_done(self):
        pass

    def export_data_rows(self):
        for export in self.exports:
            yield export


def test_generator(list_of_labels):
    generator = LabelGenerator([list_of_labels[0]])

    assert next(generator) == list_of_labels[0]
    with pytest.raises(StopIteration):
        next(generator)


def test_conversion(list_of_labels):
    generator = LabelGenerator(list_of_labels)
    label_collection = generator.as_collection()
    assert len(label_collection) == len(list_of_labels)
    assert [x for x in label_collection] == list_of_labels


def test_adding_schema_ids():
    display_name = "line_feature"
    label = Label(
        data=RasterData(arr=np.ones((32, 32, 3), dtype=np.uint8)),
        annotations=[
            ObjectAnnotation(
                value=Line(
                    points=[Point(x=1, y=2), Point(x=2, y=2)]),
                display_name=display_name,
            )
        ])
    schema_id = "expected_id"
    ontology = OntologyBuilder(tools=[
        Tool(Tool.Type.LINE, name=display_name, feature_schema_id=schema_id)
    ])
    generator = LabelGenerator([label]).assign_schema_ids(ontology)
    assert next(generator).annotations[0].schema_id == schema_id
    labels = LabelCollection([label]).assign_schema_ids(ontology)
    assert next(labels).annotations[0].schema_id == schema_id
    assert labels[0].annotations[0].schema_id == schema_id


def test_adding_urls(signer):
    label = Label(data=RasterData(arr=np.random.random((32, 32,
                                                        3)).astype(np.uint8)),
                  annotations=[])
    uuid = str(uuid4())
    generator = LabelGenerator([label]).add_url_to_data(signer(uuid))
    assert label.data.url != uuid
    assert next(generator).data.url == uuid
    assert label.data.url == uuid

    label = Label(data=RasterData(arr=np.random.random((32, 32,
                                                        3)).astype(np.uint8)),
                  annotations=[])
    assert label.data.url != uuid
    labels = LabelCollection([label]).add_url_to_data(signer(uuid))
    assert label.data.url == uuid
    assert next(labels).data.url == uuid
    assert labels[0].data.url == uuid


def test_adding_to_dataset(signer):
    dataset = FakeDataset()
    label = Label(data=RasterData(arr=np.random.random((32, 32,
                                                        3)).astype(np.uint8)),
                  annotations=[])
    uuid = str(uuid4())
    generator = LabelGenerator([label]).add_to_dataset(dataset, signer(uuid))
    assert label.data.url != uuid
    generated_label = next(generator)
    assert generated_label.data.url == uuid
    assert generated_label.data.external_id != None
    assert generated_label.data.uid == dataset.uid
    assert label.data.url == uuid

    dataset = FakeDataset()
    label = Label(data=RasterData(arr=np.random.random((32, 32,
                                                        3)).astype(np.uint8)),
                  annotations=[])
    assert label.data.url != uuid
    assert label.data.external_id == None
    assert label.data.uid != dataset.uid
    labels = LabelCollection([label]).add_to_dataset(dataset, signer(uuid))
    assert label.data.url == uuid
    assert label.data.external_id != None
    assert label.data.uid == dataset.uid
    generated_label = next(labels)
    assert generated_label.data.url == uuid
    assert generated_label.data.external_id != None
    assert generated_label.data.uid == dataset.uid


def test_adding_to_masks(signer):
    label = Label(
        data=RasterData(arr=np.random.random((32, 32, 3)).astype(np.uint8)),
        annotations=[
            ObjectAnnotation(display_name="1234",
                             value=Mask(mask=RasterData(
                                 arr=np.random.random((32, 32,
                                                       3)).astype(np.uint8)),
                                        color_rgb=[255, 255, 255]))
        ])
    uuid = str(uuid4())
    generator = LabelGenerator([label]).add_url_to_masks(signer(uuid))
    assert label.annotations[0].value.mask.url != uuid
    assert next(generator).annotations[0].value.mask.url == uuid
    assert label.annotations[0].value.mask.url == uuid

    label = Label(
        data=RasterData(arr=np.random.random((32, 32, 3)).astype(np.uint8)),
        annotations=[
            ObjectAnnotation(display_name="1234",
                             value=Mask(mask=RasterData(
                                 arr=np.random.random((32, 32,
                                                       3)).astype(np.uint8)),
                                        color_rgb=[255, 255, 255]))
        ])
    assert label.annotations[0].value.mask.url != uuid
    labels = LabelCollection([label]).add_url_to_masks(signer(uuid))
    assert next(labels).annotations[0].value.mask.url == uuid
    assert labels[0].annotations[0].value.mask.url == uuid
