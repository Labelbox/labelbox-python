from typing import List, Optional, Dict, Any
from labelbox.orm.db_object import Deletable, DbObject
from labelbox.orm.model import Field
from labelbox.pagination import PaginatedCollection
from pydantic import BaseModel


class CreateProjectDomainInput(BaseModel):
    """Input for creating a new project domain."""

    name: str
    projectId: Optional[str] = None


class ProjectDomainsPaginationInput(BaseModel):
    """Input for paginating project domains query."""

    limit: int = 30
    offset: int = 0
    searchByName: Optional[str] = None
    projectIds: Optional[List[str]] = None
    includeArchived: bool = False


class ConnectProjectToDomainsInput(BaseModel):
    """Input for connecting a project to domains."""

    projectId: str
    domainIds: List[str]


class ProjectDomainsPage(BaseModel):
    """Response model for paginated project domains."""

    nodes: List["ProjectDomain"]
    totalCount: int


class ProjectDomain(DbObject, Deletable):
    """A project domain represents a categorization for projects."""

    # Fields matching the GraphQL schema
    id = Field.String("id")
    name = Field.String("name")
    createdAt = Field.DateTime("createdAt")
    updatedAt = Field.DateTime("updatedAt")
    deactivatedAt = Field.DateTime("deactivatedAt")
    ratingsCount = Field.Int("ratingsCount")

    @classmethod
    def create(
        cls, client, name: str, project_id: Optional[str] = None
    ) -> "ProjectDomain":
        """Create a new project domain.

        Args:
            client: Labelbox client instance
            name: Name of the project domain
            project_id: Optional project ID to associate with

        Returns:
            Created ProjectDomain instance
        """
        input_data = CreateProjectDomainInput(name=name, projectId=project_id)

        query_str = """
        mutation CreateProjectDomainPyApi($input: CreateProjectDomainInput!) {
            createProjectDomain(input: $input) {
                id
                name
                createdAt
                updatedAt
                deactivatedAt
                ratingsCount
            }
        }"""

        result = client.execute(query_str, {"input": input_data.model_dump()})
        return cls(client, result["createProjectDomain"])

    def activate(self) -> "ProjectDomain":
        """Activate this project domain.

        Returns:
            Updated ProjectDomain instance
        """
        query_str = """
        mutation ActivateProjectDomainPyApi($id: ID!) {
            activateProjectDomain(id: $id) {
                id
                name
                createdAt
                updatedAt
                deactivatedAt
                ratingsCount
            }
        }"""

        result = self.client.execute(query_str, {"id": self.uid})
        return self.__class__(self.client, result["activateProjectDomain"])

    def deactivate(self) -> "ProjectDomain":
        """Deactivate this project domain.

        Returns:
            Updated ProjectDomain instance
        """
        query_str = """
        mutation DeactivateProjectDomainPyApi($id: ID!) {
            deactivateProjectDomain(id: $id) {
                id
                name
                createdAt
                updatedAt
                deactivatedAt
                ratingsCount
            }
        }"""

        result = self.client.execute(query_str, {"id": self.uid})
        return self.__class__(self.client, result["deactivateProjectDomain"])

    @classmethod
    def connect_project_to_domains(
        cls, client, project_id: str, domain_ids: List[str]
    ) -> bool:
        """Connect a project to multiple domains.

        Args:
            client: Labelbox client instance
            project_id: ID of the project to connect
            domain_ids: List of domain IDs to connect to the project

        Returns:
            True if successful
        """
        input_data = ConnectProjectToDomainsInput(
            projectId=project_id, domainIds=domain_ids
        )

        query_str = """
        mutation ConnectProjectToDomainsPyApi($input: ConnectProjectToDomainsInput!) {
            connectProjectToDomains(input: $input)
        }"""

        result = client.execute(query_str, {"input": input_data.model_dump()})
        return result["connectProjectToDomains"]

    @classmethod
    def query_by_project_id(
        cls,
        project_id: str,
        limit: int = 30,
        offset: int = 0,
        include_archived: bool = False,
    ) -> str:
        """Get GraphQL query string for fetching project domains by project ID.

        Args:
            project_id: ID of the project to fetch domains for
            limit: Maximum number of results to return
            offset: Number of results to skip
            include_archived: Whether to include archived domains

        Returns:
            GraphQL query string
        """
        return """
        query ProjectDomainsPyApi($projectId: ID!, $includeArchived: Boolean!) {
            projectDomains(
                pagination: {
                    offset: %d
                    limit: %d
                    projectIds: [$projectId]
                    includeArchived: $includeArchived
                }
            ) {
                nodes {
                    id
                    name
                    createdAt
                    updatedAt
                    deactivatedAt
                    ratingsCount
                }
                totalCount
            }
        }"""

    @classmethod
    def get_by_project_id(
        cls,
        client,
        project_id: str,
        limit: int = 30,
        offset: int = 0,
        include_archived: bool = False,
    ) -> PaginatedCollection:
        """Get project domains for a specific project with pagination.

        Args:
            client: Labelbox client instance
            project_id: ID of the project to fetch domains for
            limit: Maximum number of results to return
            offset: Number of results to skip
            include_archived: Whether to include archived domains

        Returns:
            PaginatedCollection of ProjectDomain instances
        """
        query_str = cls.query_by_project_id(
            project_id, limit, offset, include_archived
        )

        params: Dict[str, Any] = {
            "projectId": project_id,
            "includeArchived": include_archived,
        }

        return PaginatedCollection(
            client=client,
            query=query_str,
            params=params,
            dereferencing=["projectDomains", "nodes"],
            obj_class=cls,
        )

    @classmethod
    def search(
        cls,
        client,
        search_by_name: Optional[str] = None,
        project_ids: Optional[List[str]] = None,
        limit: int = 30,
        offset: int = 0,
        include_archived: bool = False,
    ) -> PaginatedCollection:
        """Search project domains with various filters.

        Args:
            client: Labelbox client instance
            search_by_name: Optional name to search for
            project_ids: Optional list of project IDs to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip
            include_archived: Whether to include archived domains

        Returns:
            PaginatedCollection of ProjectDomain instances
        """
        query_str = """
        query SearchProjectDomainsPyApi($includeArchived: Boolean!, $searchByName: String, $projectIds: [ID!]) {
            projectDomains(
                pagination: {
                    offset: %d
                    limit: %d
                    searchByName: $searchByName
                    projectIds: $projectIds
                    includeArchived: $includeArchived
                }
            ) {
                nodes {
                    id
                    name
                    createdAt
                    updatedAt
                    deactivatedAt
                    ratingsCount
                }
                totalCount
            }
        }"""

        # Build params dictionary with proper types for GraphQL
        params: Dict[str, Any] = {
            "includeArchived": include_archived,
        }

        # Only add non-None values to avoid type issues
        if search_by_name is not None:
            params["searchByName"] = search_by_name
        if project_ids is not None:
            # Keep as list for GraphQL - it will be properly serialized
            params["projectIds"] = project_ids

        return PaginatedCollection(
            client=client,
            query=query_str,
            params=params,
            dereferencing=["projectDomains", "nodes"],
            obj_class=cls,
        )
