from dataclasses import dataclass
from typing import Optional, Union, Dict, Any, TYPE_CHECKING

from labelbox.utils import snake_case
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field

if TYPE_CHECKING:
    from labelbox import Client


class IAMIntegrationProvider:
    """Constants for IAM integration providers."""

    Aws = "AWS"
    Gcp = "GCP"
    Azure = "Azure"


@dataclass
class AwsIamIntegrationSettings:
    """Settings for AWS IAM integration.

    Attributes:
        role_arn: AWS role ARN
        read_bucket: Optional read bucket name
    """

    role_arn: Optional[str] = None
    read_bucket: Optional[str] = None


@dataclass
class GcpIamIntegrationSettings:
    """Settings for GCP IAM integration.

    Attributes:
        service_account_email_id: GCP service account email ID
        read_bucket: GCP read bucket name
    """

    service_account_email_id: Optional[str] = None
    read_bucket: Optional[str] = None


@dataclass
class AzureIamIntegrationSettings:
    """Settings for Azure IAM integration.

    Attributes:
        read_container_url: Azure container URL
        tenant_id: Azure tenant ID
        client_id: Azure client ID
        client_secret: Azure client secret
    """

    read_container_url: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class IAMIntegration(DbObject):
    """Represents an IAM integration for delegated access.

    Attributes:
        settings: Provider-specific settings for the integration
        name: Name of the integration
        created_at: When the integration was created
        updated_at: When the integration was last updated
        provider: The cloud provider (e.g., "AWS", "GCP", "Azure")
        valid: Whether the integration is valid
        last_valid_at: When the integration was last validated
        is_org_default: Whether this is the default integration for the organization
    """

    settings: Optional[
        Union[
            AwsIamIntegrationSettings,
            GcpIamIntegrationSettings,
            AzureIamIntegrationSettings,
        ]
    ] = None

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        """Initialize an IAM integration.

        Args:
            client: The Labelbox client
            data: The integration data from the API
        """
        settings = data.pop("settings", None)
        if settings is not None:
            type_name = settings.pop("__typename", None)
            settings = {snake_case(k): v for k, v in settings.items()}
            if type_name == "AwsIamIntegrationSettings":
                self.settings = AwsIamIntegrationSettings(**settings)
            elif type_name == "GcpIamIntegrationSettings":
                self.settings = GcpIamIntegrationSettings(**settings)
            elif type_name == "AzureIamIntegrationSettings":
                self.settings = AzureIamIntegrationSettings(**settings)
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

    @staticmethod
    def create(
        client: "Client",
        name: str,
        settings: Union[
            AwsIamIntegrationSettings,
            GcpIamIntegrationSettings,
            AzureIamIntegrationSettings,
        ],
    ) -> "IAMIntegration":
        """Creates a new IAM integration.

        Args:
            client: The Labelbox client
            name: Name of the integration
            settings: Provider-specific settings for the integration

        Returns:
            The created IAM integration

        Raises:
            ValueError: If unsupported settings type is provided
        """
        if isinstance(settings, AwsIamIntegrationSettings):
            return IAMIntegration.create_aws_integration(
                client,
                name=name,
                role_arn=settings.role_arn or "",
                read_bucket=settings.read_bucket,
            )
        elif isinstance(settings, GcpIamIntegrationSettings):
            return IAMIntegration.create_gcp_integration(
                client,
                name=name,
                read_bucket=settings.read_bucket or "",
            )
        elif isinstance(settings, AzureIamIntegrationSettings):
            return IAMIntegration.create_azure_integration(
                client,
                name=name,
                read_container_url=settings.read_container_url or "",
                tenant_id=settings.tenant_id or "",
            )
        else:
            raise ValueError(
                f"Unsupported settings type for integration creation: {type(settings).__name__}"
            )

    @staticmethod
    def create_aws_integration(
        client: "Client",
        name: str,
        role_arn: str,
        read_bucket: Optional[str] = None,
    ) -> "IAMIntegration":
        """Creates a new AWS IAM integration.

        Args:
            client: The Labelbox client
            name: Name of the integration
            role_arn: AWS role ARN
            read_bucket: Optional read bucket name

        Returns:
            The created AWS IAM integration
        """
        query_str = """
        mutation CreateAwsIamIntegrationPyApi($data: AwsIamIntegrationCreateInput!) {
            createAwsIamIntegration(data: $data) {
                id
                name
                createdAt
                updatedAt
                provider
                valid
                lastValidAt
                isOrgDefault
                settings { 
                    __typename 
                    ... on AwsIamIntegrationSettings {
                        roleArn 
                        readBucket 
                    }
                }
            }
        }
        """
        params = {
            "data": {
                "name": name,
                "roleArn": role_arn,
                "readBucket": read_bucket,
            }
        }
        res = client.execute(query_str, params)
        return IAMIntegration(client, res["createAwsIamIntegration"])

    @staticmethod
    def create_gcp_integration(
        client: "Client", name: str, read_bucket: str
    ) -> "IAMIntegration":
        """Creates a new GCP IAM integration.

        Args:
            client: The Labelbox client
            name: Name of the integration
            read_bucket: GCP read bucket name

        Returns:
            The created GCP IAM integration
        """
        query_str = """
        mutation CreateGcpIamIntegrationPyApi($data: GcpIamIntegrationCreateInput!) {
            createGcpIamIntegration(data: $data) {
                id
                name
                createdAt
                updatedAt
                provider
                valid
                lastValidAt
                isOrgDefault
                settings { 
                    __typename 
                    ... on GcpIamIntegrationSettings {
                        serviceAccountEmailId 
                        readBucket 
                    }
                }
            }
        }
        """
        params = {"data": {"name": name, "readBucket": read_bucket}}
        res = client.execute(query_str, params)
        return IAMIntegration(client, res["createGcpIamIntegration"])

    @staticmethod
    def create_azure_integration(
        client: "Client", name: str, read_container_url: str, tenant_id: str
    ) -> "IAMIntegration":
        """Creates a new Azure IAM integration.

        Args:
            client: The Labelbox client
            name: Name of the integration
            read_container_url: Azure container URL
            tenant_id: Azure tenant ID

        Returns:
            The created Azure IAM integration
        """
        query_str = """
        mutation CreateAzureIamIntegrationPyApi($data: AzureIamIntegrationCreateInput!) {
            createAzureIamIntegration(data: $data) {
                id
                name
                createdAt
                updatedAt
                provider
                valid
                lastValidAt
                isOrgDefault
                settings { 
                    __typename 
                    ... on AzureIamIntegrationSettings {
                        readContainerUrl 
                        tenantId 
                    }
                }
            }
        }
        """
        params = {
            "data": {
                "name": name,
                "readContainerUrl": read_container_url,
                "tenantId": tenant_id,
            }
        }
        res = client.execute(query_str, params)
        return IAMIntegration(client, res["createAzureIamIntegration"])

    def update(
        self,
        name: Optional[str] = None,
        settings: Optional[
            Union[
                AwsIamIntegrationSettings,
                GcpIamIntegrationSettings,
                AzureIamIntegrationSettings,
            ]
        ] = None,
    ) -> None:
        """Updates an existing IAM integration.

        Args:
            name: Optional new name for the integration
            settings: Optional new provider-specific settings for the integration

        Raises:
            ValueError: If current integration settings are missing or if settings type
                       doesn't match the integration provider
        """
        current_settings = settings or self.settings

        if not current_settings:
            raise ValueError("Current integration settings are missing.")

        if self.provider == "AWS":
            if not isinstance(current_settings, AwsIamIntegrationSettings):
                raise ValueError(
                    "Expected AwsIamIntegrationSettings for AWS provider."
                )
            self.update_aws_integration(
                name=name or self.name,
                role_arn=current_settings.role_arn or "",
                read_bucket=current_settings.read_bucket,
            )
        elif self.provider == "GCP":
            if not isinstance(current_settings, GcpIamIntegrationSettings):
                raise ValueError(
                    "Expected GcpIamIntegrationSettings for GCP provider."
                )
            self.update_gcp_integration(
                name=name or self.name,
                read_bucket=current_settings.read_bucket or "",
            )
        elif self.provider == "Azure":
            if not isinstance(current_settings, AzureIamIntegrationSettings):
                raise ValueError(
                    "Expected AzureIamIntegrationSettings for Azure provider."
                )
            self.update_azure_integration(
                name=name or self.name,
                read_container_url=current_settings.read_container_url or "",
                tenant_id=current_settings.tenant_id or "",
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def update_aws_integration(
        self, name: str, role_arn: str, read_bucket: Optional[str] = None
    ) -> None:
        """Updates an existing AWS IAM integration.

        Args:
            name: New name for the integration
            role_arn: New AWS role ARN
            read_bucket: New read bucket name
        """
        query_str = """
        mutation UpdateAwsIamIntegrationPyApi($data: AwsIamIntegrationUpdateInput!, $where: WhereUniqueIdInput!) {
            updateAwsIamIntegration(data: $data, where: $where) { id }
        }
        """
        params = {
            "data": {
                "name": name,
                "roleArn": role_arn,
                "readBucket": read_bucket,
            },
            "where": {"id": self.uid},
        }
        self.client.execute(query_str, params)

    def update_gcp_integration(self, name: str, read_bucket: str) -> None:
        """Updates an existing GCP IAM integration.

        Args:
            name: New name for the integration
            read_bucket: New read bucket name
        """
        query_str = """
        mutation UpdateGcpIamIntegrationPyApi($data: GcpIamIntegrationUpdateInput!, $where: WhereUniqueIdInput!) {
            updateGcpIamIntegration(data: $data, where: $where) { id }
        }
        """
        params = {
            "data": {"name": name, "readBucket": read_bucket},
            "where": {"id": self.uid},
        }
        self.client.execute(query_str, params)

    def update_azure_integration(
        self,
        name: str,
        read_container_url: str,
        tenant_id: str,
    ) -> None:
        """Updates an existing Azure IAM integration.

        Args:
            name: New name for the integration
            read_container_url: New Azure container URL
            tenant_id: New Azure tenant ID

        Note:
            Client credentials (client_id, client_secret) cannot be updated
            through the update API for security reasons.
        """
        query_str = """
        mutation UpdateAzureIamIntegrationPyApi($data: AzureIamIntegrationUpdateInput!, $where: WhereUniqueIdInput!) {
            updateAzureIamIntegration(data: $data, where: $where) { id }
        }
        """
        params = {
            "data": {
                "name": name,
                "readContainerUrl": read_container_url,
                "tenantId": tenant_id,
            },
            "where": {"id": self.uid},
        }

        self.client.execute(query_str, params)

    def validate(self) -> Dict[str, Any]:
        """Validates the IAM integration.

        Returns:
            Dict containing validation results with the following keys:
                - valid: Whether the integration is valid
                - checks: List of validation checks with their results
        """
        query_str = """
        mutation ValidateIamIntegrationPyApi($where: WhereUniqueIdInput!) {
            validateIamIntegration(where: $where) {
                valid
                checks { name success message }
            }
        }
        """
        params = {"where": {"id": self.uid}}
        return self.client.execute(query_str, params)["validateIamIntegration"]

    def set_as_default(self) -> None:
        """Sets this integration as the default for the organization."""
        query_str = """
        mutation SetDefaultIamIntegrationPyApi($where: WhereUniqueIdInput!) {
            setDefaultIamIntegration(where: $where) { id }
        }
        """
        params = {"where": {"id": self.uid}}
        self.client.execute(query_str, params, experimental=True)
