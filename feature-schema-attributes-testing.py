import os
from labelbox import Client
from labelbox.schema.ontology import OntologyBuilder, Tool, PromptIssueTool
from labelbox.schema.tool_building.classification import Classification, Option
from labelbox.schema.tool_building.types import FeatureSchemaAttribute
from labelbox.schema.media_type import MediaType
from labelbox.schema.ontology_kind import OntologyKind


client = Client(
    api_key=os.environ.get('STAGE_API_KEY'),
    endpoint="https://app.lb-stage.xyz/api/_gql/graphql",
    rest_endpoint="https://app.lb-stage.xyz/api/api/v1")

# client = Client(
#     api_key=os.environ.get('LOCALHOST_API_KEY'),
#     endpoint="http://localhost:8080/graphql",
#     rest_endpoint="http://localhost:3000/api/api/v1")

builder = OntologyBuilder(

  tools=[
    Tool(
      name="Auto OCR",
      tool=Tool.Type.BBOX,
      attributes=[
        FeatureSchemaAttribute(
          attributeName="auto-ocr",
          attributeValue="true"
        )
      ],
      classifications=[
        Classification(
          name="Auto ocr text class value",
          instructions="This is an auto OCR text value classification",
          class_type=Classification.Type.TEXT,
          scope=Classification.Scope.GLOBAL,
          attributes=[
            FeatureSchemaAttribute(
              attributeName="auto-ocr-text-value",
              attributeValue="true"
            )
          ]
        )
      ]
    )
  ]
)

# client.create_ontology("Auto OCR ontology from sdk", builder.asdict(), media_type=MediaType.Document)

builder = OntologyBuilder(
  classifications=[
    Classification(
      name="prompt message scope text classification",
      instructions="This is a prompt message scoped text classification",
      class_type=Classification.Type.TEXT,
      scope=Classification.Scope.INDEX,
      attributes=[
        FeatureSchemaAttribute(
          attributeName="prompt-message-scope",
          attributeValue="true"
        )
      ]
    )
  ]
)

# client.create_ontology('MMC Ontology with prompt message scope class', builder.asdict(), media_type=MediaType.Conversational, ontology_kind=OntologyKind.ModelEvaluation)

builder = OntologyBuilder(
  classifications=[
    Classification(
      name="Requires connection checklist classification",
      instructions="This is a requires connection checklist classification",
      class_type=Classification.Type.CHECKLIST,
      scope=Classification.Scope.GLOBAL,
      attributes=[
        FeatureSchemaAttribute(
          attributeName="requires-connection",
          attributeValue="true"
        )
      ],
      options=[
        Option(
          value='First option'
        ),
        Option(
          value='Second option'
        )
      ]
    )
  ]
);

# client.create_ontology('Image ontology with requires connection classes', builder.asdict(), media_type=MediaType.Image)


# feature_schema = client.upsert_feature_schema(Tool(name='Testing', tool=Tool.Type.BBOX, attributes=[FeatureSchemaAttribute(attributeName='auto-ocr', attributeValue='true')]).asdict())
# print(feature_schema)
# fetched_feature_schema = client.get_feature_schema(feature_schema.uid)
# feature_schemas_with_name = client.get_feature_schemas('Auto OCR')

# # Iterate over the feature schemas
# for schema in feature_schemas_with_name:
#     print(schema)

# ontology = client.create_ontology_from_feature_schemas('Ontology from feature schemas', ['cm4rc1nl90h36070782v9hlpt'])

# feature_schema = client.update_feature_schema_title('cm4rc1nl90h36070782v9hlpt', 'This is a new title - did it remove the feature schema attributes? UPDATED')
# client.delete_unused_feature_schema('cm4rhzhn7026e07wm2az681di')

# feature_schema = client.create_feature_schema(normalized={'tool': 'rectangle',  'name': 'cat', 'color': 'black', 'attributes': [{'attributeName': 'auto-ocr', 'attributeValue': 'true'}]})
# print(feature_schema)

# classification = Classification.from_dict({
#     "name": "Test Classification",
#     "instructions": "Test instructions",
#     "type": "text",  # or "checklist" or other valid Classification.Type values
#     "scope": "index",  # or "index" for Classification.Scope values
#     "required": False,  # optional
#     "attributes": [  # optional
#         {
#             "attributeName": "prompt-message-scope",
#             "attributeValue": "true"
#         }
#     ],
#     "options": []
# })

# tool = Tool.from_dict({
#     "name": "Test Tool",
#     "type": "rectangle",  # or "checklist" or other valid Classification.Type values
#     "required": False,  # optional
#     "attributes": [  # optional
#         {
#             "attributeName": "auto-ocr",
#             "attributeValue": "true"
#         }
#     ],
#     "options": []
# })

tool = PromptIssueTool.from_dict({
    "name": "Test Tool",
    "type": "rectangle",  # or "checklist" or other valid Classification.Type values
    "required": False,  # optional
    "attributes": [  # optional
        {
            "attributeName": "auto-ocr",
            "attributeValue": "true"
        }
    ],
    "options": [],
})

# print(tool)