import datetime
import labelbox as lb
from labelbox.client import Client
from labelbox.schema.enums import AnnotationImportState
from labelbox.schema.media_type import MediaType
from labelbox.schema.project import Project
from labelbox.types import (
    Label,
    ObjectAnnotation,
    RelationshipAnnotation,
    Relationship,
    TextEntity,
    DocumentRectangle,
    DocumentEntity,
    Point,
    Text,
    ClassificationAnnotation,
    DocumentTextSelection,
    Radio,
    ClassificationAnswer,
    Checklist,
)
from labelbox.data.serialization.ndjson import NDJsonConverter
import pytest
from ...conftest import create_dataset_robust


def validate_iso_format(date_string: str):
    parsed_t = datetime.datetime.fromisoformat(
        date_string
    )  # this will blow up if the string is not in iso format
    assert parsed_t.hour is not None
    assert parsed_t.minute is not None
    assert parsed_t.second is not None


def _get_text_relationship_label():
    ner_source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )
    ner_source2 = ObjectAnnotation(
        name="e4",
        value=TextEntity(start=40, end=70),
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

    ner_relationship3 = RelationshipAnnotation(
        name="rel3",
        value=Relationship(
            source=ner_target,  # UUID is not required for annotation types
            target=ner_source2,
            type=Relationship.Type.BIDIRECTIONAL,
        ),
    )

    return [
        ner_source,
        ner_source2,
        ner_target,
        ner_target2,
        ner_relationship1,
        ner_relationship2,
        ner_relationship3,
    ]


@pytest.fixture(scope="module", autouse=True)
def normalized_ontology_by_media_type_relationship():
    """Returns NDJSON of ontology based on media type"""

    entity_source_tool = {
        "required": False,
        "name": "e1",
        "tool": "named-entity",
        "color": "#006FA6",
        "classifications": [],
    }
    entity_target_tool = {
        "required": False,
        "name": "e2",
        "tool": "named-entity",
        "color": "#006FA6",
        "classifications": [],
    }
    entity_target_2_tool = {
        "required": False,
        "name": "e3",
        "tool": "named-entity",
        "color": "#006FA6",
        "classifications": [],
    }
    entity_source_2_tool = {
        "required": False,
        "name": "e4",
        "tool": "named-entity",
        "color": "#006FA6",
        "classifications": [],
    }
    relationship_1 = {
        "name": "rel",
        "tool": "edge",
    }
    relationship_2 = {
        "name": "rel2",
        "tool": "edge",
    }
    relationship_3 = {
        "name": "rel3",
        "tool": "edge",
    }

    return {
        MediaType.Text: {
            "tools": [
                entity_source_tool,
                entity_source_2_tool,
                entity_target_tool,
                entity_target_2_tool,
                relationship_1,
                relationship_2,
                relationship_3,
            ],
        },
    }


@pytest.fixture
def configured_project(
    client: Client,
    rand_gen,
    data_row_json_by_media_type,
    normalized_ontology_by_media_type_relationship,
    teardown_helpers,
):
    """Configure project for test. Request.param will contain the media type if not present will use Image MediaType. The project will have 10 data rows."""

    media_type = MediaType.Text

    dataset = None

    dataset = create_dataset_robust(client, name=rand_gen(str))

    project = client.create_project(
        name=f"{media_type}-{rand_gen(str)}", media_type=media_type
    )

    ontology = client.create_ontology(
        name=f"{media_type}-{rand_gen(str)}",
        normalized=normalized_ontology_by_media_type_relationship[media_type],
        media_type=media_type,
    )

    project.connect_ontology(ontology)
    data_row_data = []

    for _ in range(3):
        data_row_data.append(
            data_row_json_by_media_type[media_type](rand_gen(str))
        )

    task = dataset.create_data_rows(data_row_data)
    task.wait_till_done()
    global_keys = [row["global_key"] for row in task.result]
    data_row_ids = [row["id"] for row in task.result]

    project.create_batch(
        rand_gen(str),
        data_row_ids,  # sample of data row objects
        5,  # priority between 1(Highest) - 5(lowest)
    )
    project.data_row_ids = data_row_ids
    project.global_keys = global_keys

    yield project
    teardown_helpers.teardown_project_labels_ontology_feature_schemas(project)

    if dataset:
        dataset.delete()


@pytest.mark.parametrize(
    "configured_project",
    [MediaType.Text],
    indirect=["configured_project"],
)
def test_import_media_types(
    client: Client,
    configured_project: Project,
):
    labels = []
    media_type = configured_project.media_type
    for data_row in configured_project.data_row_ids:
        annotations = _get_text_relationship_label()

        label = Label(
            data={"uid": data_row},
            annotations=annotations,
        )
        labels.append(label)

    label_import = lb.MALPredictionImport.create_from_objects(
        client, configured_project.uid, f"test-import-{media_type}", labels
    )
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0


def test_valid_classification_relationships():
    def create_pdf_annotation(target_type: str) -> ObjectAnnotation:
        if target_type == "bbox":
            return ObjectAnnotation(
                name="bbox",
                value=DocumentRectangle(
                    start=Point(x=0, y=0),
                    end=Point(x=0.5, y=0.5),
                    page=1,
                    unit="PERCENT",
                ),
            )
        elif target_type == "entity":
            return ObjectAnnotation(
                name="entity",
                value=DocumentEntity(
                    page=1,
                    textSelections=[
                        DocumentTextSelection(token_ids=[], group_id="", page=1)
                    ],
                ),
            )
        raise ValueError(f"Unknown target type: {target_type}")

    def verify_relationship(
        source: ClassificationAnnotation, target: ObjectAnnotation
    ):
        relationship = RelationshipAnnotation(
            name="relationship",
            value=Relationship(
                source=source,
                target=target,
                type=Relationship.Type.UNIDIRECTIONAL,
            ),
        )
        label = Label(
            data={"global_key": "global_key"}, annotations=[relationship]
        )
        result = list(NDJsonConverter.serialize([label]))
        assert len(result) == 1

    # Test case 1: Text Classification -> DocumentRectangle
    text_source = ClassificationAnnotation(
        name="text", value=Text(answer="test")
    )
    verify_relationship(text_source, create_pdf_annotation("bbox"))

    # Test case 2: Text Classification -> DocumentEntity
    verify_relationship(text_source, create_pdf_annotation("entity"))

    # Test case 3: Radio Classification -> DocumentRectangle
    radio_source = ClassificationAnnotation(
        name="sub_radio_question",
        value=Radio(
            answer=ClassificationAnswer(
                name="first_sub_radio_answer",
                classifications=[
                    ClassificationAnnotation(
                        name="second_sub_radio_question",
                        value=Radio(
                            answer=ClassificationAnswer(
                                name="second_sub_radio_answer"
                            )
                        ),
                    )
                ],
            )
        ),
    )
    verify_relationship(radio_source, create_pdf_annotation("bbox"))

    # Test case 4: Checklist Classification -> DocumentEntity
    checklist_source = ClassificationAnnotation(
        name="sub_checklist_question",
        value=Checklist(
            answer=[ClassificationAnswer(name="first_sub_checklist_answer")]
        ),
    )
    verify_relationship(checklist_source, create_pdf_annotation("entity"))


def test_classification_relationship_restrictions():
    """Test all relationship validation error messages."""
    text = ClassificationAnnotation(name="text", value=Text(answer="test"))
    point = ObjectAnnotation(name="point", value=Point(x=1, y=1))

    # Test case: Classification -> Point (invalid)
    # Should fail because classifications can only connect to PDF targets
    relationship = RelationshipAnnotation(
        name="relationship",
        value=Relationship(
            source=text,
            target=point,
            type=Relationship.Type.UNIDIRECTIONAL,
        ),
    )

    with pytest.raises(
        TypeError,
        match="Unable to create relationship with non ObjectAnnotation source: .*",
    ):
        label = Label(
            data={"global_key": "test_key"}, annotations=[relationship]
        )
        list(NDJsonConverter.serialize([label]))


def test_relationship_readonly_default_none():
    """Test that relationship readonly field defaults to None when not specified."""
    source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )
    target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    relationship = RelationshipAnnotation(
        name="rel",
        value=Relationship(
            source=source,
            target=target,
            type=Relationship.Type.UNIDIRECTIONAL,
        ),
    )
    assert relationship.value.readonly is None


def test_relationship_readonly_explicit_false():
    """Test that relationship readonly field can be explicitly set to False."""
    source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )
    target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    relationship = RelationshipAnnotation(
        name="rel",
        value=Relationship(
            source=source,
            target=target,
            type=Relationship.Type.UNIDIRECTIONAL,
            readonly=False,
        ),
    )
    assert relationship.value.readonly is False


def test_relationship_readonly_explicit_true():
    """Test that setting relationship readonly=True triggers a warning."""
    source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )
    target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    with pytest.warns(
        UserWarning,
        match="Creating a relationship with readonly=True is in beta.*",
    ):
        relationship = RelationshipAnnotation(
            name="rel",
            value=Relationship(
                source=source,
                target=target,
                type=Relationship.Type.UNIDIRECTIONAL,
                readonly=True,
            ),
        )
    assert relationship.value.readonly is True


def test_relationship_source_ontology_name():
    """Test that relationship can be created with source_ontology_name instead of source."""
    target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    relationship = RelationshipAnnotation(
        name="rel",
        value=Relationship(
            source_ontology_name="test_source",
            target=target,
            type=Relationship.Type.UNIDIRECTIONAL,
        ),
    )
    assert relationship.value.source_ontology_name == "test_source"
    assert relationship.value.source is None


def test_relationship_missing_source_validation():
    """Test that relationship requires either source or source_ontology_name."""
    target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    with pytest.raises(
        ValueError,
        match="Either source or source_ontology_name must be provided",
    ):
        RelationshipAnnotation(
            name="rel",
            value=Relationship(
                target=target,
                type=Relationship.Type.UNIDIRECTIONAL,
            ),
        )


def test_relationship_both_sources_validation():
    """Test that relationship cannot have both source and source_ontology_name."""
    source = ObjectAnnotation(
        name="e1",
        value=TextEntity(start=10, end=12),
    )
    target = ObjectAnnotation(
        name="e2",
        value=TextEntity(start=30, end=35),
    )

    with pytest.raises(
        ValueError,
        match="Only one of 'source' or 'source_ontology_name' may be provided",
    ):
        RelationshipAnnotation(
            name="rel",
            value=Relationship(
                source=source,
                source_ontology_name="test_source",
                target=target,
                type=Relationship.Type.UNIDIRECTIONAL,
            ),
        )
