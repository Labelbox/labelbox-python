import pytest

from labelbox import Tool, MediaType

point = Tool(
    tool=Tool.Type.POINT,
    name="name",
    color="#ff0000",
)


def test_deletes_a_feature_schema(client):
    tool = client.upsert_feature_schema(point.asdict())

    assert (
        client.delete_unused_feature_schema(tool.normalized["featureSchemaId"])
        is None
    )


def test_cant_delete_already_deleted_feature_schema(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized["featureSchemaId"]

    client.delete_unused_feature_schema(feature_schema_id) is None

    with pytest.raises(
        Exception,
        match="Failed to delete the feature schema, message: Feature schema is already deleted",
    ):
        client.delete_unused_feature_schema(feature_schema_id)


def test_cant_delete_feature_schema_with_ontology(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized["featureSchemaId"]
    ontology = client.create_ontology_from_feature_schemas(
        name="ontology name",
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image,
    )

    with pytest.raises(
        Exception,
        match="Failed to delete the feature schema, message: Feature schema cannot be deleted because it is used in ontologies",
    ):
        client.delete_unused_feature_schema(feature_schema_id)

    client.delete_unused_ontology(ontology.uid)
    client.delete_unused_feature_schema(feature_schema_id)


def test_throws_an_error_if_feature_schema_to_delete_doesnt_exist(client):
    with pytest.raises(
        Exception,
        match="Failed to delete the feature schema, message: Cannot find root schema node with feature schema id doesntexist",
    ):
        client.delete_unused_feature_schema("doesntexist")


def test_updates_a_feature_schema_title(client, feature_schema):
    feature_schema_id = feature_schema.normalized["featureSchemaId"]
    new_title = "new title"
    updated_feature_schema = client.update_feature_schema_title(
        feature_schema_id, new_title
    )

    assert updated_feature_schema.normalized["name"] == new_title


def test_throws_an_error_when_updating_a_feature_schema_with_empty_title(
    client, feature_schema
):
    tool = feature_schema
    feature_schema_id = tool.normalized["featureSchemaId"]

    with pytest.raises(Exception):
        client.update_feature_schema_title(feature_schema_id, "")


def test_throws_an_error_when_updating_not_existing_feature_schema(client):
    with pytest.raises(Exception):
        client.update_feature_schema_title("doesntexist", "new title")


def test_creates_a_new_feature_schema(feature_schema):
    assert feature_schema.uid is not None


def test_updates_a_feature_schema(client, feature_schema):
    created_feature_schema = feature_schema
    tool_to_update = Tool(
        tool=Tool.Type.POINT,
        name="new name",
        color="#ff0000",
        feature_schema_id=created_feature_schema.normalized["featureSchemaId"],
    )
    updated_feature_schema = client.upsert_feature_schema(
        tool_to_update.asdict()
    )

    assert updated_feature_schema.normalized["name"] == "new name"


def test_does_not_include_used_feature_schema(client, feature_schema):
    tool = feature_schema
    feature_schema_id = tool.normalized["featureSchemaId"]
    ontology = client.create_ontology_from_feature_schemas(
        name="ontology name",
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image,
    )
    unused_feature_schemas = client.get_unused_feature_schemas()

    assert feature_schema_id not in unused_feature_schemas

    client.delete_unused_ontology(ontology.uid)
