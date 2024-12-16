import os
from libs.labelbox.src.labelbox import Client
from libs.labelbox.src.labelbox.schema.ontology import OntologyBuilder, Tool
from libs.labelbox.src.labelbox.schema.tool_building.classification import Classification, Option
from libs.labelbox.src.labelbox.schema.tool_building.types import FeatureSchemaAttribute
from libs.labelbox.src.labelbox.schema.media_type import MediaType
from libs.labelbox.src.labelbox.schema.ontology_kind import OntologyKind
import json


# client = Client(
#     api_key=os.environ.get('STAGE_API_KEY'),
#     endpoint="https://app.lb-stage.xyz/api/_gql/graphql",
#     rest_endpoint="https://app.lb-stage.xyz/api/api/v1")

client = Client(
    api_key=os.environ.get('LOCALHOST_API_KEY'),
    endpoint="http://localhost:8080/graphql",
    rest_endpoint="http://localhost:3000/api/api/v1")

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

# client.create_ontology("Auto OCR ontology", builder.asdict(), media_type=MediaType.Document)

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
          attributeName="required-connection",
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


feature_schema = client.upsert_feature_schema(Tool(name='Auto OCR from upsert feature schema', tool=Tool.Type.BBOX, attributes=[FeatureSchemaAttribute(attributeName='auto-ocr', attributeValue='true')]).asdict())
fetched_feature_schema = client.get_feature_schema(feature_schema.uid)
feature_schemas_with_name = client.get_feature_schemas('Auto OCR')

# Iterate over the feature schemas
for schema in feature_schemas_with_name:
    print(schema)
