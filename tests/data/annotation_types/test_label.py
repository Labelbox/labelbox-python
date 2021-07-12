from labelbox.data.annotation_types.classification.classification import Classification, ClassificationAnswer, Radio, Subclass
from labelbox.data.annotation_types.annotation import Annotation
from labelbox.data.annotation_types.geometry import Point, Line
import numpy as np

from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.schema.ontology import OntologyBuilder, Tool, Classification as OClassification, Option


def test_schema_assignment_geometry():
    display_name = "line_feature"
    label = Label(
        data=RasterData(arr=np.ones((32, 32, 3), dtype=np.uint8)),
        annotations=[
            Annotation(
                value=Line(
                    points=[Point(x=1, y=2), Point(x=2, y=2)]),
                display_name=display_name,
            )
        ])
    schema_id = "expected_id"
    ontology = OntologyBuilder(tools=[
        Tool(Tool.Type.LINE, name=display_name, feature_schema_id=schema_id)
    ])
    label.assign_schema_ids(ontology)
    assert label.annotations[0].schema_id == schema_id


def test_schema_assignment_classification():
    radio_display_name = "radio_display_name"
    option_display_name = "my_option"
    classification = Classification(value=Radio(answer=ClassificationAnswer(
        display_name=option_display_name)),)
    label = Label(data=RasterData(arr=np.ones((32, 32, 3), dtype=np.uint8)),
                  annotations=[
                      Annotation(value=classification,
                                 display_name=radio_display_name)
                  ])
    classification_schema_id = "classification_id"
    option_schema_id = "option_schema_id"
    ontology = OntologyBuilder(
        tools=[],
        classifications=[
            OClassification(class_type=OClassification.Type.RADIO,
                            instructions=radio_display_name,
                            feature_schema_id=classification_schema_id,
                            options=[
                                Option(value=option_display_name,
                                       feature_schema_id=option_schema_id)
                            ])
        ])
    label.assign_schema_ids(ontology)
    assert label.annotations[0].schema_id == classification_schema_id
    assert label.annotations[0].value.value.answer.schema_id == option_schema_id


def test_schema_assignment_subclass():
    display_name = "line_feature"
    radio_display_name = "radio_display_name"
    option_display_name = "my_option"
    classification = Subclass(
        display_name=radio_display_name,
        value=Radio(answer=ClassificationAnswer(
            display_name=option_display_name)),
    )
    label = Label(
        data=RasterData(arr=np.ones((32, 32, 3), dtype=np.uint8)),
        annotations=[
            Annotation(value=Line(
                points=[Point(x=1, y=2), Point(x=2, y=2)]),
                       display_name=display_name,
                       classifications=[classification])
        ])
    schema_id = "expected_id"
    classification_schema_id = "classification_id"
    option_schema_id = "option_schema_id"
    ontology = OntologyBuilder(tools=[
        Tool(Tool.Type.LINE,
             name=display_name,
             feature_schema_id=schema_id,
             classifications=[
                 OClassification(class_type=OClassification.Type.RADIO,
                                 instructions=radio_display_name,
                                 feature_schema_id=classification_schema_id,
                                 options=[
                                     Option(value=option_display_name,
                                            feature_schema_id=option_schema_id)
                                 ])
             ])
    ])
    label.assign_schema_ids(ontology)
    assert label.annotations[0].schema_id == schema_id
    assert label.annotations[0].classifications[
        0].schema_id == classification_schema_id
    assert label.annotations[0].classifications[
        0].value.answer.schema_id == option_schema_id
