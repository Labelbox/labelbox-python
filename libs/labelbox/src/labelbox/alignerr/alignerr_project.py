from enum import Enum
from typing import TYPE_CHECKING, Optional

import logging

from labelbox.alignerr.schema.project_rate import ProjectRateV2
from labelbox.alignerr.schema.project_domain import ProjectDomain
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
        """Get all domains associated with this project.

        Returns:
            PaginatedCollection of ProjectDomain instances
        """
        return ProjectDomain.get_by_project_id(
            client=self.client, project_id=self.project.uid
        )

    def add_domain(self, project_domain: ProjectDomain):
        return ProjectDomain.connect_project_to_domains(
            client=self.client,
            project_id=self.project.uid,
            domain_ids=[project_domain.uid],
        )

    def get_project_rate(self) -> Optional["ProjectRateV2"]:
        return ProjectRateV2.get_by_project_id(
            client=self.client, project_id=self.project.uid
        )

    def set_project_rate(self, project_rate_input):
        return ProjectRateV2.set_project_rate(
            client=self.client,
            project_id=self.project.uid,
            project_rate_input=project_rate_input,
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
