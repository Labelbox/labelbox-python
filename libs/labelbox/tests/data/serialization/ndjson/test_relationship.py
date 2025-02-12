from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import (
    Label,
    ObjectAnnotation,
    RelationshipAnnotation,
    Relationship,
    TextEntity,
    DocumentRectangle,
    RectangleUnit,
    Point,
)


def test_unidirectional_relationship():
    ner_source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )

    ner_target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    ner_target2 = ObjectAnnotation(
        name="e3",
        value=TextEntity(start=40, end=60),
    )

    ner_relationship1 = RelationshipAnnotation(
        name="rel",
        value=Relationship(
            source=ner_source,  # UUID is not required for annotation types
            target=ner_target,
            type=Relationship.Type.UNIDIRECTIONAL,
        ),
    )

    ner_relationship2 = RelationshipAnnotation(
        name="rel2",
        value=Relationship(
            source=ner_source,  # UUID is not required for annotation types
            target=ner_target2,
            type=Relationship.Type.UNIDIRECTIONAL,
        ),
    )

    label = Label(
        data={"uid": "clqbkpy236syk07978v3pscw1"},
        annotations=[
            ner_source,
            ner_target,
            ner_target2,
            ner_relationship1,
            ner_relationship2,
        ],
    )

    serialized_label = list(NDJsonConverter.serialize([label]))

    ner_source_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_source.name
    )
    ner_target_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_target.name
    )
    ner_target_2_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_target2.name
    )
    rel_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_relationship1.name
    )
    rel_2_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_relationship2.name
    )

    assert (
        rel_serialized["relationship"]["source"]
        == ner_source_serialized["uuid"]
    )
    assert (
        rel_serialized["relationship"]["target"]
        == ner_target_serialized["uuid"]
    )
    assert (
        rel_2_serialized["relationship"]["source"]
        == ner_source_serialized["uuid"]
    )
    assert (
        rel_2_serialized["relationship"]["target"]
        == ner_target_2_serialized["uuid"]
    )
    assert rel_serialized["relationship"]["type"] == "unidirectional"
    assert rel_2_serialized["relationship"]["type"] == "unidirectional"


def test_bidirectional_relationship():
    ner_source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )

    ner_target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    ner_target2 = ObjectAnnotation(
        name="e3",
        value=TextEntity(start=40, end=60),
    )

    ner_relationship1 = RelationshipAnnotation(
        name="rel",
        value=Relationship(
            source=ner_source,  # UUID is not required for annotation types
            target=ner_target,
            type=Relationship.Type.BIDIRECTIONAL,
        ),
    )

    ner_relationship2 = RelationshipAnnotation(
        name="rel2",
        value=Relationship(
            source=ner_source,  # UUID is not required for annotation types
            target=ner_target2,
            type=Relationship.Type.BIDIRECTIONAL,
        ),
    )

    label = Label(
        data={"uid": "clqbkpy236syk07978v3pscw1"},
        annotations=[
            ner_source,
            ner_target,
            ner_target2,
            ner_relationship1,
            ner_relationship2,
        ],
    )

    serialized_label = list(NDJsonConverter.serialize([label]))

    ner_source_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_source.name
    )
    ner_target_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_target.name
    )
    ner_target_2_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_target2.name
    )
    rel_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_relationship1.name
    )
    rel_2_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_relationship2.name
    )

    assert (
        rel_serialized["relationship"]["source"]
        == ner_source_serialized["uuid"]
    )
    assert (
        rel_serialized["relationship"]["target"]
        == ner_target_serialized["uuid"]
    )
    assert (
        rel_2_serialized["relationship"]["source"]
        == ner_source_serialized["uuid"]
    )
    assert (
        rel_2_serialized["relationship"]["target"]
        == ner_target_2_serialized["uuid"]
    )
    assert rel_serialized["relationship"]["type"] == "bidirectional"
    assert rel_2_serialized["relationship"]["type"] == "bidirectional"


def test_readonly_relationships():
    ner_source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )

    ner_target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    # Test unidirectional relationship with readonly=True
    readonly_relationship = RelationshipAnnotation(
        name="readonly_rel",
        value=Relationship(
            source=ner_source,
            target=ner_target,
            type=Relationship.Type.UNIDIRECTIONAL,
            readonly=True,
        ),
    )

    # Test bidirectional relationship with readonly=False
    non_readonly_relationship = RelationshipAnnotation(
        name="non_readonly_rel",
        value=Relationship(
            source=ner_source,
            target=ner_target,
            type=Relationship.Type.BIDIRECTIONAL,
            readonly=False,
        ),
    )

    label = Label(
        data={"uid": "clqbkpy236syk07978v3pscw1"},
        annotations=[
            ner_source,
            ner_target,
            readonly_relationship,
            non_readonly_relationship,
        ],
    )

    serialized_label = list(NDJsonConverter.serialize([label]))

    ner_source_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_source.name
    )
    ner_target_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_target.name
    )
    readonly_rel_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == readonly_relationship.name
    )
    non_readonly_rel_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == non_readonly_relationship.name
    )

    # Verify readonly relationship
    assert (
        readonly_rel_serialized["relationship"]["source"]
        == ner_source_serialized["uuid"]
    )
    assert (
        readonly_rel_serialized["relationship"]["target"]
        == ner_target_serialized["uuid"]
    )
    assert readonly_rel_serialized["relationship"]["type"] == "unidirectional"
    assert readonly_rel_serialized["relationship"]["readonly"] is True

    # Verify non-readonly relationship
    assert (
        non_readonly_rel_serialized["relationship"]["source"]
        == ner_source_serialized["uuid"]
    )
    assert (
        non_readonly_rel_serialized["relationship"]["target"]
        == ner_target_serialized["uuid"]
    )
    assert (
        non_readonly_rel_serialized["relationship"]["type"] == "bidirectional"
    )
    assert non_readonly_rel_serialized["relationship"]["readonly"] is False


def test_source_ontology_name_relationship():
    ner_source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )

    ner_target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    # Test relationship with source
    regular_relationship = RelationshipAnnotation(
        name="regular_rel",
        value=Relationship(
            source=ner_source,
            target=ner_target,
            type=Relationship.Type.UNIDIRECTIONAL,
        ),
    )

    # Test relationship with source_ontology_name for PDF target
    pdf_target = ObjectAnnotation(
        name="pdf_region",
        value=DocumentRectangle(
            start=Point(x=0.5, y=0.5),
            end=Point(x=0.7, y=0.7),
            page=1,
            unit=RectangleUnit.PERCENT,
        ),
    )

    ontology_relationship = RelationshipAnnotation(
        name="ontology_rel",
        value=Relationship(
            source_ontology_name="Person",
            target=pdf_target,
            type=Relationship.Type.UNIDIRECTIONAL,
        ),
    )

    label = Label(
        data={"uid": "clqbkpy236syk07978v3pscw1"},
        annotations=[
            ner_source,
            ner_target,
            pdf_target,
            regular_relationship,
            ontology_relationship,
        ],
    )

    serialized_label = list(NDJsonConverter.serialize([label]))

    ner_source_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_source.name
    )
    ner_target_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ner_target.name
    )
    pdf_target_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == pdf_target.name
    )
    regular_rel_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == regular_relationship.name
    )
    ontology_rel_serialized = next(
        annotation
        for annotation in serialized_label
        if annotation["name"] == ontology_relationship.name
    )

    # Verify regular relationship
    assert (
        regular_rel_serialized["relationship"]["source"]
        == ner_source_serialized["uuid"]
    )
    assert (
        regular_rel_serialized["relationship"]["target"]
        == ner_target_serialized["uuid"]
    )
    assert regular_rel_serialized["relationship"]["type"] == "unidirectional"

    # Verify relationship with source_ontology_name
    assert (
        ontology_rel_serialized["relationship"]["sourceOntologyName"]
        == "Person"
    )
    assert (
        ontology_rel_serialized["relationship"]["target"]
        == pdf_target_serialized["uuid"]
    )
    assert ontology_rel_serialized["relationship"]["type"] == "unidirectional"

    # Test that providing both source and source_ontology_name raises an error
    try:
        RelationshipAnnotation(
            name="invalid_rel",
            value=Relationship(
                source=ner_source,
                source_ontology_name="Person",
                target=pdf_target,
                type=Relationship.Type.UNIDIRECTIONAL,
            ),
        )
        assert False, "Expected ValueError for providing both source and source_ontology_name"
    except Exception as e:
        assert (
            "Value error, Only one of 'source' or 'source_ontology_name' may be provided"
            in str(e)
        )

    # Test that providing neither source nor source_ontology_name raises an error
    try:
        RelationshipAnnotation(
            name="invalid_rel",
            value=Relationship(
                target=pdf_target,
                type=Relationship.Type.UNIDIRECTIONAL,
            ),
        )
        assert False, "Expected ValueError for providing neither source nor source_ontology_name"
    except Exception as e:
        assert (
            "Value error, Either source or source_ontology_name must be provided"
            in str(e)
        )
