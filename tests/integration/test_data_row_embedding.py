import pytest

import labelbox.exceptions

CUSTOM_EMD_NAME = 'custom_embedding_sdk_integration_testing'
CUSTOM_EMD_DIMS = 16


@pytest.fixture
def mdo1(client):
    yield client.get_data_row_embedding()


def test_create_then_delete_custom_embedding(mdo1):
    created_embedding = mdo1.create_custom_embedding(CUSTOM_EMD_NAME,
                                                     CUSTOM_EMD_DIMS)
    assert created_embedding['name'] == CUSTOM_EMD_NAME
    assert created_embedding['dims'] == CUSTOM_EMD_DIMS
    mdo1.delete_custom_embedding(created_embedding['id'])


def test_get_and_create_duplicated_custom_embedding(mdo1):
    embedding_list = mdo1.get_all_custom_embeddings()
    if embedding_list:
        with pytest.raises(labelbox.exceptions.LabelboxError):
            mdo1.create_custom_embedding(embedding_list[0]['name'],
                                         embedding_list[0]['dims'])
