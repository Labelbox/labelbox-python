from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest

from labelbox.data.annotation_types import (
    LabelGenerator,
    ObjectAnnotation,
    Mask,
    Label,
    GenericDataRowData,
    MaskData,
)


@pytest.fixture
def list_of_labels():
    return [
        Label(data=GenericDataRowData(uid="http://someurl")) for _ in range(5)
    ]


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
                SimpleNamespace(
                    row_data=arg["row_data"],
                    external_id=arg["external_id"],
                    uid=self.uid,
                )
            )
        return self

    def wait_till_done(self):
        pass


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


def test_adding_to_masks(signer):
    label = Label(
        data=GenericDataRowData(uid="12345"),
        annotations=[
            ObjectAnnotation(
                name="1234",
                value=Mask(
                    mask=MaskData(
                        arr=np.random.random((32, 32, 3)).astype(np.uint8)
                    ),
                    color=[255, 255, 255],
                ),
            )
        ],
    )
    uuid = str(uuid4())
    generator = LabelGenerator([label]).add_url_to_masks(signer(uuid))
    assert label.annotations[0].value.mask.url != uuid
    assert next(generator).annotations[0].value.mask.url == uuid
    assert label.annotations[0].value.mask.url == uuid
