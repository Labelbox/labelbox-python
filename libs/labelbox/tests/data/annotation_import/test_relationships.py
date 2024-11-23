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
)
import pytest


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

    dataset = client.create_dataset(name=rand_gen(str))

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
