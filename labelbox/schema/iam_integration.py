from labelbox.utils import camel_case
from pydantic import BaseModel

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field





class AwsIamIntegrationSettings(BaseModel):
    role_arn: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case


class GcpIamIntegrationSettings(BaseModel):
    service_account_email_id: str
    read_bucket: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case



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

    def __init__(self, client, data):
        settings = data.pop('settings', {})
        type_name = settings.pop('__typename')
        if type_name == "GcpIamIntegrationSettings":
            self.settings = GcpIamIntegrationSettings(**settings)
        elif type_name == "AwsIamIntegrationSettings":
            self.settings = AwsIamIntegrationSettings(**settings)

        super().__init__(client, data)

    _DEFAULT = "DEFAULT"

    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    updated_at = Field.DateTime("updated_at")
    provider = Field.String("provider")
    valid = Field.Boolean("valid")
    last_valid_at = Field.DateTime("last_valid_at")
    is_org_default = Field.Boolean("is_org_default")
