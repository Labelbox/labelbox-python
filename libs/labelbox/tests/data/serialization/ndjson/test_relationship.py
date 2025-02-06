from labelbox.data.serialization.ndjson.converter import NDJsonConverter
from labelbox.types import (
    Label,
    ObjectAnnotation,
    RelationshipAnnotation,
    Relationship,
    TextEntity,
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
