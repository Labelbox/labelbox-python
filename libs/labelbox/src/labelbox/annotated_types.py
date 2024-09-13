from typing_extensions import Annotated

from pydantic import Field


Cuid = Annotated[str, Field(min_length=25, max_length=25)]
