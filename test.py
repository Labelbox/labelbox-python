import labelbox as lb
from pprint import pprint
from api_key import API_KEY
client = lb.Client(API_KEY)

ontology_builder = lb.OntologyBuilder(
    classifications=[
        lb.Classification(
            class_type=lb.Classification.Type.CHECKLIST,
            name="nested_checklist_question",
        
            options=[
                lb.Option(
                    "first_checklist_answer",
                    options=[
                        lb.Classification(
                            class_type=lb.Classification.Type.CHECKLIST,
                            name="sub_checklist_question",
                            options=[lb.Option("first_sub_checklist_answer")],
                            ui_mode=None
                            ),
                        
                    ])
            ],
            ui_mode=lb.Classification.UIMode.SEARCHABLE),
    ]
)
ontology_builder_2 = lb.OntologyBuilder(
    classifications=[
        lb.Classification(
            class_type=lb.Classification.Type.TEXT,
            name="nested_checklist_question",
            ui_mode=lb.Classification.UIMode.SEARCHABLE),
    ]
)

text = lb.Classification(
            class_type=lb.Classification.Type.TEXT,
            name="nested_checklist_question",
            ui_mode=lb.Classification.UIMode.SEARCHABLE)
pprint(ontology_builder.asdict())

pprint(ontology_builder_2.asdict())

print(text.ui_mode)
# ontology = client.create_ontology(name="test_editor_one_nested", normalized=ontology_builder.asdict(), media_type=lb.MediaType.Image)