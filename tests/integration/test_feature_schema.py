import pytest

from labelbox import Tool, MediaType, Classification, Option

point = Tool(
    tool=Tool.Type.POINT,
    name="name",
)

TOOL_COLOR = "#ff0000"
TOOL_NAMES = {
    "bbox", "polygon", "segmentation", "line", "point", "ner",
    "raster-segmentation"
}
CLASSIFICATION_NAMES = {
    "text",
    "radio",
    "checklist",
}


@pytest.fixture
def tools():
    return {
        "bbox":
            Tool(tool=Tool.Type.BBOX,
                 name="bbox",
                 color=TOOL_COLOR,
                 required=True),
        "polygon":
            Tool(tool=Tool.Type.POLYGON, name="polygon", color=TOOL_COLOR),
        "segmentation":
            Tool(tool=Tool.Type.SEGMENTATION,
                 name="segmentation",
                 color=TOOL_COLOR),
        "point":
            Tool(tool=Tool.Type.POINT, name="point", color=TOOL_COLOR),
        "line":
            Tool(tool=Tool.Type.LINE, name="line", color=TOOL_COLOR),
        "ner":
            Tool(tool=Tool.Type.NER,
                 name="ner",
                 required=True,
                 color=TOOL_COLOR),
        "raster-seg":
            Tool(tool=Tool.Type.RASTER_SEGMENTATION,
                 name="raster-segmentation",
                 color=TOOL_COLOR)
    }


@pytest.fixture
def classifications():
    return {
        "text":
            Classification(class_type=Classification.Type.TEXT,
                           name="text",
                           required=True),
        "radio":
            Classification(class_type=Classification.Type.RADIO,
                           name="radio",
                           options=[Option("poodle")],
                           required=True),
        "checklist":
            Classification(class_type=Classification.Type.CHECKLIST,
                           name="checklist",
                           options=[Option("at_park"),
                                    Option("has_leash")])
    }


def test_deletes_a_feature_schema(client, tools):
    """
    This test covers both creation and deletion of the feature schemas.
    """
    for tool in tools.values():
        feature = client.upsert_feature_schema(tool.asdict())

        assert feature.uid is not None
        assert feature.name in TOOL_NAMES

        assert client.delete_unused_feature_schema(
            feature.normalized['featureSchemaId']) is None


def test_creates_and_deletes_classifications(client, classifications):
    """
    This test covers both creation and deletion of the classifications for feature schemas.
    """
    ...
    for classification in classifications.values():
        feature = client.upsert_feature_schema(classification.asdict())

        assert feature.uid is not None
        assert feature.name in CLASSIFICATION_NAMES

        assert client.delete_unused_feature_schema(
            feature.normalized['featureSchemaId']) is None


def test_throws_error_when_not_converted_to_dict(client, tools,
                                                 classifications):
    """
    This test covers whether or not expected error is raised when Tool/Classification object
    is not converted to dict() with .asdict() method before upserting feature schema.
    """
    with pytest.raises(AttributeError,
                       match="'Tool' object has no attribute 'get'"):
        client.upsert_feature_schema(tools["point"])

    with pytest.raises(AttributeError):
        client.upsert_feature_schema(classifications["radio"])


def test_can_retrieve_feature(client, tools):
    feature = client.upsert_feature_schema(tools["bbox"].asdict())
    assert feature.uid is not None

    get_feature = client.get_feature_schema(feature.uid)
    assert get_feature is not None

    client.delete_unused_feature_schema(feature.normalized["featureSchemaId"])


def test_returns_empty_list_if_name_doesnt_match_features(client):
    assert len(list(client.get_feature_schemas("no-feature"))) == 0


def test_cant_delete_already_deleted_feature_schema(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']

    client.delete_unused_feature_schema(feature_schema_id) is None

    with pytest.raises(
            Exception,
            match=
            "Failed to delete the feature schema, message: Feature schema is already deleted"
    ):
        client.delete_unused_feature_schema(feature_schema_id)


def test_cant_delete_feature_schema_with_ontology(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']
    ontology = client.create_ontology_from_feature_schemas(
        name='ontology name',
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image)

    with pytest.raises(
            Exception,
            match=
            "Failed to delete the feature schema, message: Feature schema cannot be deleted because it is used in ontologies"
    ):
        client.delete_unused_feature_schema(feature_schema_id)

    client.delete_unused_ontology(ontology.uid)
    client.delete_unused_feature_schema(feature_schema_id)


def test_throws_an_error_if_feature_schema_to_delete_doesnt_exist(client):
    with pytest.raises(
            Exception,
            match=
            "Failed to delete the feature schema, message: Cannot find root schema node with feature schema id doesntexist"
    ):
        client.delete_unused_feature_schema("doesntexist")


def test_updates_a_feature_schema_title(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']
    new_title = "new title"
    updated_feature_schema = client.update_feature_schema_title(
        feature_schema_id, new_title)

    assert updated_feature_schema.normalized['name'] == new_title

    client.delete_unused_feature_schema(feature_schema_id)


def test_throws_an_error_when_updating_a_feature_schema_with_empty_title(
        client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']

    with pytest.raises(Exception):
        client.update_feature_schema_title(feature_schema_id, "")

    client.delete_unused_feature_schema(feature_schema_id)


def test_throws_an_error_when_updating_not_existing_feature_schema(client):
    with pytest.raises(Exception):
        client.update_feature_schema_title("doesntexist", "new title")


def test_updates_a_feature_schema(client):
    tool = Tool(
        tool=Tool.Type.POINT,
        name="name",
        color="#ff0000",
    )
    created_feature_schema = client.upsert_feature_schema(tool.asdict())
    tool_to_update = Tool(
        tool=Tool.Type.POINT,
        name="new name",
        color="#ff0000",
        feature_schema_id=created_feature_schema.normalized['featureSchemaId'],
    )
    updated_feature_schema = client.upsert_feature_schema(
        tool_to_update.asdict())

    assert updated_feature_schema.normalized['name'] == "new name"


def test_does_not_include_used_feature_schema(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']
    ontology = client.create_ontology_from_feature_schemas(
        name='ontology name',
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image)
    unused_feature_schemas = client.get_unused_feature_schemas()

    assert feature_schema_id not in unused_feature_schemas

    client.delete_unused_ontology(ontology.uid)
    client.delete_unused_feature_schema(feature_schema_id)
