from labelbox.schema.identifiables import GlobalKeys, UniqueIds


def test_unique_ids():
    ids = ["a", "b", "c"]
    identifiables = UniqueIds(ids)
    assert [i for i in identifiables] == ids
    assert identifiables.id_type == "ID"
    assert len(identifiables) == 3


def test_global_keys():
    ids = ["a", "b", "c"]
    identifiables = GlobalKeys(ids)
    assert [i for i in identifiables] == ids
    assert identifiables.id_type == "GKEY"
    assert len(identifiables) == 3


def test_index_access():
    ids = ["a", "b", "c"]
    identifiables = GlobalKeys(ids)
    assert identifiables[0] == "a"
    assert identifiables[1:3] == GlobalKeys(["b", "c"])


def test_repr():
    ids = ["a", "b", "c"]
    identifiables = GlobalKeys(ids)
    assert repr(identifiables) == "GlobalKeys(['a', 'b', 'c'])"

    ids = ["a", "b", "c"]
    identifiables = UniqueIds(ids)
    assert repr(identifiables) == "UniqueIds(['a', 'b', 'c'])"
