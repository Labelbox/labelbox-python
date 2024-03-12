import pytest
from unittest.mock import MagicMock

from labelbox.schema.data_row import DataRow
from labelbox.schema.identifiable import GlobalKey, UniqueId
from labelbox.schema.project import validate_labeling_parameter_overrides


def test_validate_labeling_parameter_overrides_valid_data():
    mock_data_row = MagicMock(spec=DataRow)
    mock_data_row.uid = "abc"
    data = [(mock_data_row, 1), (UniqueId("efg"), 2), (GlobalKey("hij"), 3)]
    validate_labeling_parameter_overrides(data)


def test_validate_labeling_parameter_overrides_invalid_data():
    data = [("abc", 1), (UniqueId("efg"), 2), (GlobalKey("hij"), 3)]
    with pytest.raises(TypeError):
        validate_labeling_parameter_overrides(data)


def test_validate_labeling_parameter_overrides_invalid_priority():
    mock_data_row = MagicMock(spec=DataRow)
    mock_data_row.uid = "abc"
    data = [(mock_data_row, "invalid"), (UniqueId("efg"), 2),
            (GlobalKey("hij"), 3)]
    with pytest.raises(TypeError):
        validate_labeling_parameter_overrides(data)


def test_validate_labeling_parameter_overrides_invalid_tuple_length():
    mock_data_row = MagicMock(spec=DataRow)
    mock_data_row.uid = "abc"
    data = [(mock_data_row, "invalid"), (UniqueId("efg"), 2),
            (GlobalKey("hij"))]
    with pytest.raises(TypeError):
        validate_labeling_parameter_overrides(data)
