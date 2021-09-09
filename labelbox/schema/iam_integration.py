from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class IAMIntegration(DbObject):
    """ Represents an IAM integration for delegated access

    Attributes:
        name (str)
        updated_at (datetime)
        created_at (datetime)
        provider (str)
        valid (bool)
        last_valid_at (datetime)
        is_org_default (boolean)

    """

    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    updated_at = Field.DateTime("updated_at")
    provider = Field.String("provider")
    valid = Field.Boolean("valid")
    last_valid_at = Field.DateTime("last_valid_at")
    is_org_default = Field.Boolean("is_org_default")
