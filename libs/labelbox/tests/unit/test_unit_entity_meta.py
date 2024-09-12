import pytest

from labelbox.orm.model import Relationship
from labelbox.orm.db_object import DbObject


def test_illegal_cache_cond1():
    class TestEntityA(DbObject):
        test_entity_b = Relationship.ToOne("TestEntityB", cache=True)

    with pytest.raises(TypeError) as exc_info:

        class TestEntityB(DbObject):
            another_entity = Relationship.ToOne("AnotherEntity", cache=True)

    assert (
        "`test_entity_a` caches `test_entity_b` which caches `['another_entity']`"
        in str(exc_info.value)
    )


def test_illegal_cache_cond2():
    class TestEntityD(DbObject):
        another_entity = Relationship.ToOne("AnotherEntity", cache=True)

    with pytest.raises(TypeError) as exc_info:

        class TestEntityC(DbObject):
            test_entity_d = Relationship.ToOne("TestEntityD", cache=True)

    assert (
        "`test_entity_c` caches `test_entity_d` which caches `['another_entity']`"
        in str(exc_info.value)
    )
