from re import U

from labelbox.schema.data_row_metadata import _DeleteBatchDataRowMetadata
from labelbox.schema.identifiable import GlobalKey, UniqueId


def test_dict_delete_data_row_batch():
    obj = _DeleteBatchDataRowMetadata(
        data_row_identifier=UniqueId("abcd"),
        schema_ids=["clqh77tyk000008l2a9mjesa1", "clqh784br000008jy0yuq04fy"],
    )
    assert obj.model_dump() == {
        "data_row_identifier": {"id": "abcd", "id_type": "ID"},
        "schema_ids": [
            "clqh77tyk000008l2a9mjesa1",
            "clqh784br000008jy0yuq04fy",
        ],
    }

    obj = _DeleteBatchDataRowMetadata(
        data_row_identifier=GlobalKey("fegh"),
        schema_ids=["clqh77tyk000008l2a9mjesa1", "clqh784br000008jy0yuq04fy"],
    )
    assert obj.model_dump() == {
        "data_row_identifier": {"id": "fegh", "id_type": "GKEY"},
        "schema_ids": [
            "clqh77tyk000008l2a9mjesa1",
            "clqh784br000008jy0yuq04fy",
        ],
    }


def test_dict_delete_data_row_batch_by_alias():
    obj = _DeleteBatchDataRowMetadata(
        data_row_identifier=UniqueId("abcd"),
        schema_ids=["clqh77tyk000008l2a9mjesa1", "clqh784br000008jy0yuq04fy"],
    )
    assert obj.model_dump(by_alias=True) == {
        "dataRowIdentifier": {"id": "abcd", "idType": "ID"},
        "schemaIds": ["clqh77tyk000008l2a9mjesa1", "clqh784br000008jy0yuq04fy"],
    }

    obj = _DeleteBatchDataRowMetadata(
        data_row_identifier=GlobalKey("fegh"),
        schema_ids=["clqh77tyk000008l2a9mjesa1", "clqh784br000008jy0yuq04fy"],
    )
    assert obj.model_dump(by_alias=True) == {
        "dataRowIdentifier": {"id": "fegh", "idType": "GKEY"},
        "schemaIds": ["clqh77tyk000008l2a9mjesa1", "clqh784br000008jy0yuq04fy"],
    }
