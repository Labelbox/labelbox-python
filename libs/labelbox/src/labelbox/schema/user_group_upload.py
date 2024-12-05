from typing import List, Optional

from lbox.exceptions import ResourceNotFoundError

from labelbox.client import Client
from labelbox.pagination import PaginatedCollection


class UserGroupUpload:
    def __init__(self, client: Client):
        self.client = client

    def upload_members(self, group_id: str, role: str, emails: List[str]):
        role_id = self._get_role_id(role)
        if role_id is None:
            raise ResourceNotFoundError(message="The role does not exist.")

    def _get_role_id(self, role_name: str) -> Optional[str]:
        role_id = None
        query = """query GetAvailableUserRolesPyPi {
                    roles(skip: %d, first: %d) {
                        id
                        organizationId
                        name
                        description
                    }
                }
            """

        result = PaginatedCollection(
            client=self.client,
            query=query,
            params={},
            dereferencing=["roles"],
            obj_class=lambda _, data: data,  # type: ignore
        )
        if result is None:
            raise ResourceNotFoundError(
                message="Could not find any valid roles."
            )
        for role in result:
            if role["name"].strip() == role_name.strip():
                role_id = role["id"]
                break

        return role_id
