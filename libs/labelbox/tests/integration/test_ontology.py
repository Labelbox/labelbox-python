import pytest

from labelbox import OntologyBuilder, MediaType, Tool
from labelbox.orm.model import Entity
import json
import time

from labelbox.schema.queue_mode import QueueMode


def test_feature_schema_is_not_archived(client, ontology):
    feature_schema_to_check = ontology.normalized['tools'][0]
    result = client.is_feature_schema_archived(
        ontology.uid, feature_schema_to_check['featureSchemaId'])
    assert result == False


def test_feature_schema_is_archived(client, configured_project_with_label):
    project, _, _, label = configured_project_with_label
    ontology = project.ontology()
    feature_schema_id = ontology.normalized['tools'][0]['featureSchemaId']
    result = client.delete_feature_schema_from_ontology(ontology.uid,
                                                        feature_schema_id)
    assert result.archived == True and result.deleted == False
    assert client.is_feature_schema_archived(ontology.uid,
                                             feature_schema_id) == True


def test_is_feature_schema_archived_for_non_existing_feature_schema(
        client, ontology):
    with pytest.raises(
            Exception,
            match="The specified feature schema was not in the ontology"):
        client.is_feature_schema_archived(ontology.uid,
                                          'invalid-feature-schema-id')


def test_is_feature_schema_archived_for_non_existing_ontology(client, ontology):
    feature_schema_to_unarchive = ontology.normalized['tools'][0]
    with pytest.raises(
            Exception,
            match="Resource 'Ontology' not found for params: 'invalid-ontology'"
    ):
        client.is_feature_schema_archived(
            'invalid-ontology', feature_schema_to_unarchive['featureSchemaId'])


def test_delete_tool_feature_from_ontology(client, ontology):
    feature_schema_to_delete = ontology.normalized['tools'][0]
    assert len(ontology.normalized['tools']) == 2
    result = client.delete_feature_schema_from_ontology(
        ontology.uid, feature_schema_to_delete['featureSchemaId'])
    assert result.deleted == True
    assert result.archived == False
    updatedOntology = client.get_ontology(ontology.uid)
    assert len(updatedOntology.normalized['tools']) == 1


@pytest.mark.skip(reason="normalized ontology contains Relationship, "
                  "which is not finalized yet. introduce this back when"
                  "Relationship feature is complete and we introduce"
                  "a Relationship object to the ontology that we can parse")
def test_from_project_ontology(project) -> None:
    o = OntologyBuilder.from_project(project)
    assert o.asdict() == project.ontology().normalized


point = Tool(
    tool=Tool.Type.POINT,
    name="name",
    color="#ff0000",
)


def test_deletes_an_ontology(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']
    ontology = client.create_ontology_from_feature_schemas(
        name='ontology name',
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image)

    assert client.delete_unused_ontology(ontology.uid) is None

    client.delete_unused_feature_schema(feature_schema_id)


def test_cant_delete_an_ontology_with_project(client):
    project = client.create_project(name="test project",
                                    queue_mode=QueueMode.Batch,
                                    media_type=MediaType.Image)
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']
    ontology = client.create_ontology_from_feature_schemas(
        name='ontology name',
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image)
    project.connect_ontology(ontology)

    with pytest.raises(
            Exception,
            match=
            "Failed to delete the ontology, message: Cannot delete an ontology connected to a project. The ontology is connected to projects: "
            + project.uid):
        client.delete_unused_ontology(ontology.uid)

    project.delete()
    client.delete_unused_ontology(ontology.uid)
    client.delete_unused_feature_schema(feature_schema_id)


def test_inserts_a_feature_schema_at_given_position(client):
    tool1 = {'tool': 'polygon', 'name': 'tool1', 'color': 'blue'}
    tool2 = {'tool': 'polygon', 'name': 'tool2', 'color': 'blue'}
    ontology_normalized_json = {"tools": [tool1, tool2], "classifications": []}
    ontology = client.create_ontology(name="ontology",
                                      normalized=ontology_normalized_json,
                                      media_type=MediaType.Image)
    created_feature_schema = client.upsert_feature_schema(point.asdict())
    client.insert_feature_schema_into_ontology(
        created_feature_schema.normalized['featureSchemaId'], ontology.uid, 1)
    ontology = client.get_ontology(ontology.uid)

    assert ontology.normalized['tools'][1][
        'schemaNodeId'] == created_feature_schema.normalized['schemaNodeId']

    client.delete_unused_ontology(ontology.uid)


def test_moves_already_added_feature_schema_in_ontology(client):
    tool1 = {'tool': 'polygon', 'name': 'tool1', 'color': 'blue'}
    ontology_normalized_json = {"tools": [tool1], "classifications": []}
    ontology = client.create_ontology(name="ontology",
                                      normalized=ontology_normalized_json,
                                      media_type=MediaType.Image)
    created_feature_schema = client.upsert_feature_schema(point.asdict())
    feature_schema_id = created_feature_schema.normalized['featureSchemaId']
    client.insert_feature_schema_into_ontology(feature_schema_id, ontology.uid,
                                               1)
    ontology = client.get_ontology(ontology.uid)
    assert ontology.normalized['tools'][1][
        'schemaNodeId'] == created_feature_schema.normalized['schemaNodeId']
    client.insert_feature_schema_into_ontology(feature_schema_id, ontology.uid,
                                               0)
    ontology = client.get_ontology(ontology.uid)

    assert ontology.normalized['tools'][0][
        'schemaNodeId'] == created_feature_schema.normalized['schemaNodeId']

    client.delete_unused_ontology(ontology.uid)


def test_does_not_include_used_ontologies(client):
    tool = client.upsert_feature_schema(point.asdict())
    feature_schema_id = tool.normalized['featureSchemaId']
    ontology_with_project = client.create_ontology_from_feature_schemas(
        name='ontology name',
        feature_schema_ids=[feature_schema_id],
        media_type=MediaType.Image)
    project = client.create_project(name="test project",
                                    queue_mode=QueueMode.Batch,
                                    media_type=MediaType.Image)
    project.connect_ontology(ontology_with_project)
    unused_ontologies = client.get_unused_ontologies()

    assert ontology_with_project.uid not in unused_ontologies

    project.delete()
    client.delete_unused_ontology(ontology_with_project.uid)
    client.delete_unused_feature_schema(feature_schema_id)


def _get_attr_stringify_json(obj, attr):
    value = getattr(obj, attr.name)
    if attr.field_type.name.lower() == "json":
        return json.dumps(value, sort_keys=True)
    return value


def test_feature_schema_create_read(client, rand_gen):
    name = f"test-root-schema-{rand_gen(str)}"
    feature_schema_cat_normalized = {
        'tool': 'polygon',
        'name': name,
        'color': 'black',
        'classifications': [],
    }
    created_feature_schema = client.create_feature_schema(
        feature_schema_cat_normalized)
    queried_feature_schema = client.get_feature_schema(
        created_feature_schema.uid)
    for attr in Entity.FeatureSchema.fields():
        assert _get_attr_stringify_json(created_feature_schema,
                                        attr) == _get_attr_stringify_json(
                                            queried_feature_schema, attr)

    time.sleep(3)  # Slight delay for searching
    queried_feature_schemas = list(client.get_feature_schemas(name))
    assert [feature_schema.name for feature_schema in queried_feature_schemas
           ] == [name]
    queried_feature_schema = queried_feature_schemas[0]

    for attr in Entity.FeatureSchema.fields():
        assert _get_attr_stringify_json(created_feature_schema,
                                        attr) == _get_attr_stringify_json(
                                            queried_feature_schema, attr)


def test_ontology_create_read(client, rand_gen):
    ontology_name = f"test-ontology-{rand_gen(str)}"
    tool_name = f"test-ontology-tool-{rand_gen(str)}"
    feature_schema_cat_normalized = {
        'tool': 'polygon',
        'name': tool_name,
        'color': 'black',
        'classifications': [],
    }
    feature_schema = client.create_feature_schema(feature_schema_cat_normalized)
    created_ontology = client.create_ontology_from_feature_schemas(
        name=ontology_name,
        feature_schema_ids=[feature_schema.uid],
        media_type=MediaType.Image)
    tool_normalized = created_ontology.normalized['tools'][0]
    for k, v in feature_schema_cat_normalized.items():
        assert tool_normalized[k] == v
    assert tool_normalized['schemaNodeId'] is not None
    assert tool_normalized['featureSchemaId'] == feature_schema.uid

    queried_ontology = client.get_ontology(created_ontology.uid)

    for attr in Entity.Ontology.fields():
        assert _get_attr_stringify_json(created_ontology,
                                        attr) == _get_attr_stringify_json(
                                            queried_ontology, attr)

    time.sleep(3)  # Slight delay for searching
    queried_ontologies = list(client.get_ontologies(ontology_name))
    assert [ontology.name for ontology in queried_ontologies] == [ontology_name]
    queried_ontology = queried_ontologies[0]
    for attr in Entity.Ontology.fields():
        assert _get_attr_stringify_json(created_ontology,
                                        attr) == _get_attr_stringify_json(
                                            queried_ontology, attr)


def test_unarchive_feature_schema_node(client, ontology):
    feature_schema_to_unarchive = ontology.normalized['tools'][0]
    result = client.unarchive_feature_schema_node(
        ontology.uid, feature_schema_to_unarchive['featureSchemaId'])
    assert result == None


def test_unarchive_feature_schema_node_for_non_existing_feature_schema(
        client, ontology):
    with pytest.raises(
            Exception,
            match=
            "Failed to find feature schema node by id: invalid-feature-schema-id"
    ):
        client.unarchive_feature_schema_node(ontology.uid,
                                             'invalid-feature-schema-id')


def test_unarchive_feature_schema_node_for_non_existing_ontology(
        client, ontology):
    feature_schema_to_unarchive = ontology.normalized['tools'][0]
    with pytest.raises(Exception,
                       match="Failed to find ontology by id: invalid-ontology"):
        client.unarchive_feature_schema_node(
            'invalid-ontology', feature_schema_to_unarchive['featureSchemaId'])
