from typing import Optional
from labelbox import Client, CatalogSlice


def _create_catalog_slice(
    client: Client, name: str, description: Optional[str] = None
) -> str:
    """Creates a catalog slice for testing purposes.

    Args:
        client (Client): Labelbox client instance
        name (str): Name of the catalog slice
        description (str): Description of the catalog slice

    Returns:
        str: ID of the created catalog slice
    """

    mutation = """mutation CreateCatalogSlicePyApi($name: String!, $description: String, $query: SearchServiceQuery!, $sorting: [SearchServiceSorting!]) {
    createCatalogSavedQuery(
        args: {name: $name, description: $description, filter: $query, sorting: $sorting}
      ) {
        id
        name
        description
        filter
        sorting
        catalogCount {
          count
        }
      }
    }
    """

    params = {
        "description": description,
        "name": name,
        "query": [
            {
                "type": "media_attribute_asset_type",
                "assetType": {"type": "asset_type", "assetTypes": ["image"]},
            }
        ],
        "sorting": [
            {
                "field": {
                    "field": "dataRowCreatedAt",
                    "verboseName": "Created At",
                },
                "direction": "DESC",
                "metadataSchemaId": None,
            }
        ],
    }

    result = client.execute(mutation, params, experimental=True)

    return result["createCatalogSavedQuery"].get("id")


def _delete_catalog_slice(client, slice_id: str) -> bool:
    mutation = """mutation DeleteCatalogSlicePyApi($id: ID!) {
    deleteSavedQuery(args: { id: $id }) {
      success
    }
  }
  """

    params = {"id": slice_id}

    operation_done = True
    try:
        client.execute(mutation, params, experimental=True)
    except Exception as ex:
        operation_done = False

    return operation_done


def test_get_slice(client):
    # Pre-cleaning
    slices = (
        s
        for s in client.get_catalog_slices()
        if s.name in ["Test Slice 1", "Test Slice 2"]
    )
    for slice in slices:
        _delete_catalog_slice(client, slice.uid)

    # Create slices
    slice_id_1 = _create_catalog_slice(
        client, "Test Slice 1", "Slice created for SDK test."
    )
    slice_id_2 = _create_catalog_slice(
        client, "Test Slice 2", "Slice created for SDK test."
    )
    # Create slice 2b - with the same name as slice 2
    slice_id_2b = _create_catalog_slice(
        client, "Test Slice 2", "Slice created for SDK test."
    )

    # Assert get slice 1 by ID
    slice_1 = client.get_catalog_slice(slice_id_1)
    assert isinstance(slice_1, CatalogSlice)

    slice_1 = client.get_catalog_slice(slice_name="Test Slice 1")
    assert isinstance(slice_1, CatalogSlice)

    slices_2 = client.get_catalog_slice(slice_name="Test Slice 2")
    assert len(slices_2) == 2
    assert isinstance(slices_2, list) and all(
        [isinstance(item, CatalogSlice) for item in slices_2]
    )

    # Cleaning - Delete slices
    _delete_catalog_slice(client, slice_id_1)
    _delete_catalog_slice(client, slice_id_2)
    _delete_catalog_slice(client, slice_id_2b)
