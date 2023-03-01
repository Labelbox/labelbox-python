from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest

from labelbox.data.annotation_types import (LabelGenerator, ObjectAnnotation,
                                            ImageData, MaskData, Line, Mask,
                                            Point, Label)
from labelbox import OntologyBuilder, Tool


@pytest.fixture
def list_of_labels():
    return [Label(data=ImageData(url="http://someurl")) for _ in range(5)]


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
                SimpleNamespace(row_data=arg['row_data'],
                                external_id=arg['external_id'],
                                uid=self.uid))
        return self

    def wait_till_done(self):
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
    label_collection = list(generator)
    assert len(label_collection) == len(list_of_labels)
    assert [x for x in label_collection] == list_of_labels


def test_adding_schema_ids():
    name = "line_feature"
    label = Label(
        data=ImageData(arr=np.ones((32, 32, 3), dtype=np.uint8)),
        annotations=[
            ObjectAnnotation(
                value=Line(
                    points=[Point(x=1, y=2), Point(x=2, y=2)]),
                name=name,
            )
        ])
    feature_schema_id = "expected_id"
    ontology = OntologyBuilder(tools=[
        Tool(Tool.Type.LINE, name=name, feature_schema_id=feature_schema_id)
    ])
    generator = LabelGenerator([label]).assign_feature_schema_ids(ontology)
    assert next(generator).annotations[0].feature_schema_id == feature_schema_id


def test_adding_urls(signer):
    label = Label(data=ImageData(arr=np.random.random((32, 32,
                                                       3)).astype(np.uint8)),
                  annotations=[])
    uuid = str(uuid4())
    generator = LabelGenerator([label]).add_url_to_data(signer(uuid))
    assert label.data.url != uuid
    assert next(generator).data.url == uuid
    assert label.data.url == uuid


def test_adding_to_dataset(signer):
    dataset = FakeDataset()
    label = Label(data=ImageData(arr=np.random.random((32, 32,
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


def test_adding_to_masks(signer):
    label = Label(
        data=ImageData(arr=np.random.random((32, 32, 3)).astype(np.uint8)),
        annotations=[
            ObjectAnnotation(name="1234",
                             value=Mask(mask=MaskData(
                                 arr=np.random.random((32, 32,
                                                       3)).astype(np.uint8)),
                                        color=[255, 255, 255]))
        ])
    uuid = str(uuid4())
    generator = LabelGenerator([label]).add_url_to_masks(signer(uuid))
    assert label.annotations[0].value.mask.url != uuid
    assert next(generator).annotations[0].value.mask.url == uuid
    assert label.annotations[0].value.mask.url == uuid
