from labelbox.pydantic_compat import BaseModel

class ExternalWorkforce(BaseModel):
    """
    Represents an external workforce used in the Labelbox system.

    Attributes:
        id (str): The unique identifier of the external workforce.
        name (str): The name of the external workforce.
    """
    id: str
    name: str
