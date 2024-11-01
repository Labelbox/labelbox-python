from typing import Annotated, Type

from pydantic import StringConstraints

FeatureSchemaId: Type[str] = Annotated[
    str, StringConstraints(min_length=25, max_length=25)
]
SchemaId: Type[str] = Annotated[
    str, StringConstraints(min_length=25, max_length=25)
]
