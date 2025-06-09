from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import logging

from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.schema.timeunit import TimeUnit
from lbox.exceptions import LabelboxError

from labelbox.schema.user import User
from labelbox.schema.role import Role

if TYPE_CHECKING:
    from labelbox import Client

logger = logging.getLogger(__name__)


class ApiKey(DbObject):
    """Represents an API key in the Labelbox system.

    API keys are used for authentication with the Labelbox API. Each key is associated
    with a specific user and has properties like expiration time and revocation status.

    Attributes:
        name (str): The name of the API key
        created_at (datetime): When the API key was created
        updated_at (datetime): When the API key was last updated
        revoked (bool): Whether the API key has been revoked
        expires_at_epoch (int): Expiration time as Unix timestamp
        created_by_user (str): ID of the user who created this API key
        user (str): ID of the user this API key belongs to
    """

    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    updated_at = Field.DateTime("updated_at")
    revoked = Field.Boolean("revoked")
    expires_at_epoch = Field.Int("expires_at_epoch")
    created_by_user_id = Field.String("created_by_user_id")
    user_id = Field.String("user_id")

    @property
    def created_by(self) -> Optional["User"]:
        """Gets the User who created this API key.

        Returns:
            Optional[User]: The User who created this API key, or None if not available.
        """
        if not hasattr(self, "_created_by"):
            # Use created_by_user_id if present, otherwise fall back to user_id
            # (typically needed for older API keys where created_by_user_id is NULL)
            user_id_to_fetch = (
                self.created_by_user_id
                if self.created_by_user_id is not None
                else self.user_id
            )
            self._created_by = (
                self.client._get_single(User, user_id_to_fetch)
                if user_id_to_fetch
                else None
            )

        return self._created_by

    @property
    def created_for(self) -> Optional["User"]:
        """Gets the User this API key was created for.

        Returns:
            Optional[User]: The User this API key belongs to, or None if not available
        """
        if not hasattr(self, "_created_for"):
            self._created_for = (
                self.client._get_single(User, self.user_id)
                if self.user_id
                else None
            )
        return self._created_for

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize an ApiKey object.

        Args:
            *args: Variable length argument list passed to parent class
            **kwargs: Arbitrary keyword arguments passed to parent class
        """
        super().__init__(*args, **kwargs)
        self.expired_at = datetime.fromtimestamp(
            int(self.expires_at_epoch), tz=timezone.utc
        )

    def revoke(self) -> Dict[str, Any]:
        """Revokes this API key, making it invalid for authentication.

        This method marks the API key as revoked in the Labelbox system.
        Once revoked, the API key can no longer be used for authentication.

        Returns:
            Dict[str, Any]: The response from the server containing the ID of the revoked API key.

        Example:
            >>> client = Client(api_key="your_api_key")
            >>> api_key = client.get_api_key("api_key_id")
            >>> api_key.revoke()
        """
        mutation = """mutation DeleteApiKeyPyApi($id: ID!) {
            updateApiKey(where: { id: $id }, data: { revoked: true }) {
                id
            }
        }
        """
        try:
            result = self.client.execute(mutation, {"id": self.uid})
        except Exception as e:
            raise LabelboxError(f"Failed to revoke API key: {str(e)}") from e

        if (
            not result
            or "updateApiKey" not in result
            or not result["updateApiKey"].get("id")
        ):
            raise LabelboxError(
                "API key revocation failed: no update information returned."
            )
        return result

    @staticmethod
    def _get_current_user_permissions(client: "Client") -> List[str]:
        """Retrieve current user permissions from the client's organization role with caching.

        Args:
            client: The Labelbox client instance.

        Returns:
            List[str]: A list of permission strings associated with the current user's role.
        """
        if hasattr(client, "_cached_current_user_permissions"):
            return client._cached_current_user_permissions

        query = """
        query GetUserPermissionsPyApi($userId: ID) {
          organizationRole(userId: $userId) {
            permissions
          }
        }
        """

        response = client.execute(query)
        perms = response["organizationRole"]["permissions"]
        client._cached_current_user_permissions = perms

        return perms

    @staticmethod
    def get_api_keys(
        client: "Client", include_expired: bool = False
    ) -> List["ApiKey"]:
        """Retrieves all API keys accessible to the current user using the provided client.

        Args:
            client: The Labelbox client instance.
            include_expired (bool, optional): Whether to include expired API keys.
                Defaults to False (only non-expired keys are returned).

        Returns:
            List[ApiKey]: List of API key objects
        """
        query_str = """
        query GetUsersApiKeysPyApi {
            user {
                id
                apiKeys {
                    id
                    name
                    createdAt
                    updatedAt
                    revoked
                    expiresAtEpoch
                    userId
                    userEmail
                    createdByUserId
                }
                apiKeysOtherUsers {
                    id
                    name
                    userId
                    createdAt
                    updatedAt
                    revoked
                    expiresAtEpoch
                    createdByUserId
                    userEmail
                }
            }
        }
        """

        response = client.execute(query_str)

        if not response or "user" not in response:
            return []

        all_keys = []
        current_time = datetime.now(timezone.utc)

        for key_data in response["user"].get("apiKeys", []):
            api_key = ApiKey(client, key_data)
            # Only add if we want to include expired keys OR if the key has not expired.
            if include_expired or api_key.expired_at > current_time:
                all_keys.append(api_key)

        for key_data in response["user"].get("apiKeysOtherUsers", []):
            api_key = ApiKey(client, key_data)
            if include_expired or api_key.expired_at > current_time:
                all_keys.append(api_key)

        return all_keys

    @staticmethod
    def _get_available_api_key_roles(client: "Client") -> List[str]:
        """Get the list of built-in roles available for API key creation with caching.

        This method retrieves all roles available in the organization and filters them
        based on the current user's permissions. The results are cached on the client
        to avoid redundant API calls.

        Args:
            client: The Labelbox client instance.

        Returns:
            List[str]: A list of role names that can be assigned to API keys.

        Raises:
            LabelboxError: If there's an error retrieving the user permissions.
        """
        if hasattr(client, "_cached_available_api_key_roles"):
            return client._cached_available_api_key_roles
        try:
            current_permissions = ApiKey._get_current_user_permissions(client)
        except Exception as e:
            raise LabelboxError(
                f"Error getting current user permissions: {str(e)}"
            )
        query = """
        query GetAvailableUserRolesPyApi {
          roles {
            name
            permissions
            organizationId
          }
        }
        """
        response = client.execute(query)
        all_roles = response["roles"]
        available_roles = []
        for role in all_roles:
            if role["name"] in ["None", "Tenant Admin"]:
                continue
            if all(perm in current_permissions for perm in role["permissions"]):
                available_roles.append(role["name"])
        client._cached_available_api_key_roles = available_roles
        return available_roles

    @staticmethod
    def _get_user(client: "Client", email: str) -> Optional[str]:
        """Checks if a user with the given email exists in the organization.

        Args:
            client: The Labelbox client instance.
            email (str): Email address of the user to check for.

        Returns:
            Optional[str]: The user ID if found, None otherwise.
        """
        try:
            # Use existing Organization.users() method to find user by email
            org = client.get_organization()
            users = org.users(where=User.email == email)

            # Return the first matching user's ID if found
            user = next(users, None)
            return user.uid if user else None

        except Exception as e:
            raise LabelboxError(
                f"Error retrieving user with email '{email}': {str(e)}"
            )

    @staticmethod
    def create_api_key(
        client: "Client",
        name: str,
        user: Union["User", str],
        role: Union["Role", str],
        validity: int = 0,
        time_unit: TimeUnit = TimeUnit.SECOND,
    ) -> Dict[str, str]:
        """Creates a new API key using the provided client.

        Args:
            client: The Labelbox client instance.
            name (str): Name of the API key
            user (Union[User, str]): User object or email for whom to create the API key
            role (Union[Role, str]): Permission role for the API key (Role enum or string)
            validity (int, optional): Validity period value (must be positive). Defaults to 0.
            time_unit (TimeUnit, optional): Time unit for validity period. Defaults to TimeUnit.SECOND.

        Returns:
            Dict[str, str]: Dictionary containing the created API key details including id and jwt

        Raises:
            ValueError: If invalid parameters are provided
            LabelboxError: If the API request fails or there are permission issues
        """
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")

        user_email = user.email if hasattr(user, "email") else user
        if not user_email or not isinstance(user_email, str):
            raise ValueError("user must be a User object or a valid email")

        # Check if the user exists in the organization
        user_id = ApiKey._get_user(client, user_email)
        if not user_id:
            raise ValueError(
                f"User with email '{user_email}' does not exist in the organization"
            )

        role_name = role.name if hasattr(role, "name") else role
        if not role_name or not isinstance(role_name, str):
            raise ValueError("role must be a Role object or a valid role name")

        allowed_roles = ApiKey._get_available_api_key_roles(client)
        # Normalize the allowed roles to lowercase for case-insensitive comparison
        normalized_allowed_roles = [r.lower() for r in allowed_roles]
        if role_name.lower() not in normalized_allowed_roles:
            raise ValueError(
                f"Invalid role specified. Allowed roles are: {allowed_roles}"
            )

        validity_seconds = 0
        if validity < 0:
            raise ValueError("validity must be a positive integer")

        if not isinstance(time_unit, TimeUnit):
            raise ValueError("time_unit must be a valid TimeUnit enum value")

        validity_seconds = validity * time_unit.value

        if validity_seconds < TimeUnit.MINUTE.value:
            raise ValueError("Minimum validity period is 1 minute")

        max_seconds = 25 * TimeUnit.WEEK.value
        if validity_seconds > max_seconds:
            raise ValueError(
                "Maximum validity period is 6 months (or 25 weeks)"
            )

        query_str = """
         mutation CreateUserApiKeyPyApi($name: String!, $userEmail: String!, $role: String, $validitySeconds: Int) {
             createApiKey(
                 data: { name: $name, targetUserEmailId: $userEmail, role: $role, validitySeconds: $validitySeconds }
             ) {
                 id  
                 jwt
             }
         }
         """

        params = {
            "name": name,
            "userEmail": user_email,
            "role": role_name,
            "validitySeconds": validity_seconds,
        }

        try:
            result = client.execute(query_str, params)
            api_key_result = result.get("createApiKey")

            if not api_key_result:
                raise LabelboxError(
                    "Failed to create API key. No data returned from the server."
                )

            return api_key_result

        except Exception as e:
            raise LabelboxError(str(e)) from e

    @staticmethod
    def get_api_key(client: "Client", api_key_id: str) -> Optional["ApiKey"]:
        """Retrieves a single API key by its ID using the provided client.

        Args:
            client: The Labelbox client instance.
            api_key_id (str): The unique ID of the API key.

        Returns:
            Optional[ApiKey]: The corresponding ApiKey object if found, otherwise None.
        """
        keys = ApiKey.get_api_keys(client, include_expired=True)

        return next((key for key in keys if key.uid == api_key_id), None)
