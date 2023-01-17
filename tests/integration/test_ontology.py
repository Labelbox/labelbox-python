import pytest

from labelbox import OntologyBuilder, MediaType
from labelbox.orm.model import Entity
import json
import time


@pytest.mark.skip(reason="normalized ontology contains Relationship, "
                  "which is not finalized yet. introduce this back when"
                  "Relationship feature is complete and we introduce"
                  "a Relationship object to the ontology that we can parse")
def test_from_project_ontology(project) -> None:
    o = OntologyBuilder.from_project(project)
    assert o.asdict() == project.ontology().normalized


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
