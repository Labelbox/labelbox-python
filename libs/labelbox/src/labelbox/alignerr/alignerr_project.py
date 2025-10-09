from enum import Enum
from typing import TYPE_CHECKING, Optional

import logging

from labelbox.alignerr.schema.project_rate import ProjectRateV2
from labelbox.alignerr.schema.project_domain import ProjectDomain
from labelbox.alignerr.schema.enchanced_resource_tags import (
    EnhancedResourceTag,
    ResourceTagType,
)
from labelbox.alignerr.schema.project_boost_workforce import (
    ProjectBoostWorkforce,
)
from labelbox.pagination import PaginatedCollection

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from labelbox import Client
    from labelbox.schema.project import Project
    from labelbox.alignerr.schema.project_domain import ProjectDomain


class AlignerrRole(Enum):
    Labeler = "LABELER"
    Reviewer = "REVIEWER"
    Admin = "ADMIN"


class AlignerrProject:
    def __init__(
        self, client: "Client", project: "Project", _internal: bool = False
    ):
        if not _internal:
            raise RuntimeError(
                "AlignerrProject cannot be initialized directly. "
                "Use AlignerrProjectBuilder or AlignerrProjectFactory to create instances."
            )
        self.client = client
        self.project = project

    @property
    def project(self) -> Optional["Project"]:
        return self._project

    @project.setter
    def project(self, project: "Project"):
        self._project = project

    def domains(self) -> PaginatedCollection:
        return ProjectDomain.get_by_project_id(
            client=self.client, project_id=self.project.uid
        )

    def add_domain(self, project_domain: ProjectDomain):
        return ProjectDomain.connect_project_to_domains(
            client=self.client,
            project_id=self.project.uid,
            domain_ids=[project_domain.uid],
        )

    def get_project_rates(self) -> list["ProjectRateV2"]:
        return ProjectRateV2.get_by_project_id(
            client=self.client, project_id=self.project.uid
        )

    def set_project_rate(self, project_rate_input):
        return ProjectRateV2.set_project_rate(
            client=self.client,
            project_id=self.project.uid,
            project_rate_input=project_rate_input,
        )

    def set_tags(self, tag_names: list[str], tag_type: ResourceTagType):
        # Convert tag names to tag IDs
        tag_ids = []
        for tag_name in tag_names:
            # Search for the tag by text to get its ID
            found_tags = EnhancedResourceTag.search_by_text(
                self.client, search_text=tag_name, tag_type=tag_type
            )
            if found_tags:
                tag_ids.append(found_tags[0].id)

        # Use the existing project resource tag functionality with IDs
        self.project.update_project_resource_tags(tag_ids)
        return self

    def get_tags(self) -> list[EnhancedResourceTag]:
        """Get enhanced resource tags associated with this project.

        Returns:
            List of EnhancedResourceTag instances
        """
        # Get project resource tags and convert to EnhancedResourceTag instances
        project_resource_tags = self.project.get_resource_tags()
        enhanced_tags = []
        for tag in project_resource_tags:
            # Search for the corresponding EnhancedResourceTag by text (try different types)
            found_tags = []
            for tag_type in [ResourceTagType.Default, ResourceTagType.Billing]:
                found_tags = EnhancedResourceTag.search_by_text(
                    self.client, search_text=tag.text, tag_type=tag_type
                )
                if found_tags:
                    break
            if found_tags:
                enhanced_tags.extend(found_tags)
        return enhanced_tags

    def add_tag(self, tag: EnhancedResourceTag):
        """Add a single enhanced resource tag to the project.

        Args:
            tag: EnhancedResourceTag instance to add

        Returns:
            Self for method chaining
        """
        current_tags = self.get_tags()
        current_tag_names = [t.text for t in current_tags]

        if tag.text not in current_tag_names:
            current_tag_names.append(tag.text)
            self.set_tags(current_tag_names)

        return self

    def remove_tag(self, tag: EnhancedResourceTag):
        """Remove a single enhanced resource tag from the project.

        Args:
            tag: EnhancedResourceTag instance to remove

        Returns:
            Self for method chaining
        """
        current_tags = self.get_tags()
        current_tag_names = [t.text for t in current_tags if t.uid != tag.uid]
        self.set_tags(current_tag_names)
        return self

    def get_project_owner(self) -> Optional[ProjectBoostWorkforce]:
        """Get the ProjectBoostWorkforce for this project.

        Returns:
            ProjectBoostWorkforce instance or None if not found
        """
        return ProjectBoostWorkforce.get_by_project_id(
            client=self.client, project_id=self.project.uid
        )


class AlignerrWorkspace:
    def __init__(self, client: "Client"):
        self.client = client

    def project_builder(self):
        from labelbox.alignerr.alignerr_project_builder import (
            AlignerrProjectBuilder,
        )

        return AlignerrProjectBuilder(self.client)

    def project_prototype(self):
        from labelbox.alignerr.alignerr_project_factory import (
            AlignerrProjectFactory,
        )

        return AlignerrProjectFactory(self.client)
