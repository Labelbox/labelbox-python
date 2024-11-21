from typing import Annotated

from pydantic import Field

FeatureSchemaId = Annotated[str, Field(min_length=25, max_length=25)]
SchemaId = Annotated[str, Field(min_length=25, max_length=25)]
