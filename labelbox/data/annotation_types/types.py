from pydantic import Field
from typing_extensions import Annotated

Cuid = Annotated[str, Field(min_length=25, max_length=25)]
