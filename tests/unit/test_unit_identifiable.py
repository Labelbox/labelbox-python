from labelbox.schema.identifiable import GlobalKeys, UniqueIds


def test_unique_ids():
    ids = ["a", "b", "c"]
    identifiable = UniqueIds(ids)
    assert identifiable.keys == ids
    assert identifiable._id_type == "UID"


def test_global_keys():
    ids = ["a", "b", "c"]
    identifiable = GlobalKeys(ids)
    assert identifiable.keys == ids
    assert identifiable._id_type == "GLOBAL_KEY"


def test_strings_to_identifiable_unique_id():
    ids = ["a", "b", "c"]
    identifiable = UniqueIds.strings_to_identifiable(ids)
    assert type(identifiable) == UniqueIds
    assert identifiable.keys == ids
    assert identifiable._id_type == "UID"

    ids = "a"
    identifiable = UniqueIds.strings_to_identifiable(ids)
    assert type(identifiable) == UniqueIds
    assert identifiable.keys == [ids]
    assert identifiable._id_type == "UID"


def test_strings_to_identifiable_global_key():
    ids = ["a", "b", "c"]
    identifiable = GlobalKeys.strings_to_identifiable(ids)
    assert type(identifiable) == GlobalKeys
    assert identifiable.keys == ids
    assert identifiable._id_type == "GLOBAL_KEY"

    ids = "a"
    identifiable = GlobalKeys.strings_to_identifiable(ids)
    assert type(identifiable) == GlobalKeys
    assert identifiable.keys == [ids]
    assert identifiable._id_type == "GLOBAL_KEY"


def test__str__():
    ids = ["a", "b", "c"]
    identifiable = UniqueIds(ids)
    str_representation = identifiable.__str__()
    assert str_representation == "['a', 'b', 'c']"
