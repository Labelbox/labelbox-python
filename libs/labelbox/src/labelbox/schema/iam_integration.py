from dataclasses import dataclass

from labelbox.utils import snake_case
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


@dataclass
class AwsIamIntegrationSettings:
    role_arn: str


@dataclass
class GcpIamIntegrationSettings:
    service_account_email_id: str
    read_bucket: str


class IAMIntegration(DbObject):
    """Represents an IAM integration for delegated access

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
        settings = data.pop("settings", None)
        if settings is not None:
            type_name = settings.pop("__typename")
            settings = {snake_case(k): v for k, v in settings.items()}
            if type_name == "GcpIamIntegrationSettings":
                self.settings = GcpIamIntegrationSettings(**settings)
            elif type_name == "AwsIamIntegrationSettings":
                self.settings = AwsIamIntegrationSettings(**settings)
            else:
                self.settings = None
        else:
            self.settings = None
        super().__init__(client, data)

    _DEFAULT = "DEFAULT"

    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    updated_at = Field.DateTime("updated_at")
    provider = Field.String("provider")
    valid = Field.Boolean("valid")
    last_valid_at = Field.DateTime("last_valid_at")
    is_org_default = Field.Boolean("is_org_default")
