from labelbox.schema.identifiables import GlobalKeys, UniqueIds


def test_unique_ids():
    ids = ["a", "b", "c"]
    identifiables = UniqueIds(ids)
    assert [i for i in identifiables] == ids
    assert identifiables._id_type == "UID"


def test_global_keys():
    ids = ["a", "b", "c"]
    identifiables = GlobalKeys(ids)
    assert [i for i in identifiables] == ids
    assert identifiables._id_type == "GLOBAL_KEY"
