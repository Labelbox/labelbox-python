"""IssueCategory model for the Labelbox Python SDK.

Uses ``_CamelCaseMixin`` (Pydantic) instead of ``DbObject`` / ``Updateable``
/ ``Deletable`` because the backend's GraphQL mutations use typed input objects
incompatible with the ORM's auto-generated mutations.
"""

from typing import Any

from pydantic import ConfigDict, PrivateAttr

from labelbox.utils import _CamelCaseMixin


class IssueCategory(_CamelCaseMixin):
    """A category that can be assigned to issues within a project.

    Attributes:
        id: Unique identifier.
        name: Display name.
        description: Human-readable description.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    id: str
    name: str
    description: str
    _client: Any = PrivateAttr(default=None)

    def __repr__(self) -> str:
        return "<IssueCategory ID: %s>" % self.id

    def update(self, name: str, description: str) -> "IssueCategory":
        """Update this issue category.

        Args:
            name: New name for the category.
            description: New description for the category.

        Returns:
            Updated :class:`IssueCategory` instance.
        """
        query_str = """mutation EditIssueCategoryPyApi(
            $where: WhereUniqueIdInput!,
            $data: EditIssueCategoryInput!
        ) {
            editIssueCategory(where: $where, data: $data) {
                id name description
            }
        }"""

        result = self._client.execute(
            query_str,
            {
                "where": {"id": self.id},
                "data": {"name": name, "description": description},
            },
            experimental=True,
        )

        data = result["editIssueCategory"]
        cat = IssueCategory(
            id=data["id"],
            name=data["name"],
            description=data["description"],
        )
        cat._client = self._client
        return cat

    def delete(self) -> bool:
        """Delete this issue category.

        Returns:
            ``True`` when the deletion succeeds.
        """
        query_str = """mutation DeleteIssueCategoryPyApi(
            $where: WhereUniqueIdInput!
        ) {
            deleteIssueCategory(where: $where)
        }"""

        self._client.execute(
            query_str, {"where": {"id": self.id}}, experimental=True
        )
        return True
