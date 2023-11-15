from labelbox.schema.identifiable import GlobalKeys, UniqueIds, strings_to_identifiable


def test_unique_ids():
    ids = ["a", "b", "c"]
    identifiable = UniqueIds(ids)
    assert identifiable.keys == ids
    assert identifiable.id_type == "DATA_ROW_ID"


def test_global_keys():
    ids = ["a", "b", "c"]
    identifiable = GlobalKeys(ids)
    assert identifiable.keys == ids
    assert identifiable.id_type == "GLOBAL_KEY"


def test_strings_to_identifiable():
    ids = ["a", "b", "c"]
    identifiable = strings_to_identifiable(ids)
    assert identifiable.keys == ids
    assert identifiable.id_type == "DATA_ROW_ID"

    ids = "a"
    identifiable = strings_to_identifiable(ids)
    assert identifiable.keys == [ids]
    assert identifiable.id_type == "DATA_ROW_ID"


def test__str__():
    ids = ["a", "b", "c"]
    identifiable = UniqueIds(ids)
    str_representation = identifiable.__str__()
    assert str_representation == "['a', 'b', 'c']"
