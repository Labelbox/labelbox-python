import pytest

def test_validate_metadata(datarow_metadata_ontology):
        mdo = datarow_metadata_ontology

        assert mdo.client