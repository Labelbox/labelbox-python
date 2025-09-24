import datetime
from typing import TYPE_CHECKING, Optional
import logging

from labelbox.alignerr.schema.project_rate import BillingMode
from labelbox.alignerr.schema.project_rate import ProjectRateInput
from labelbox.alignerr.schema.project_rate import ProjectRateV2
from labelbox.alignerr.schema.project_domain import ProjectDomain
from labelbox.schema.media_type import MediaType

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from labelbox import Client
    from labelbox.alignerr.alignerr_project import AlignerrProject, AlignerrRole


class AlignerrProjectBuilder:
    def __init__(self, client: "Client"):
        self.client = client
        self._alignerr_rates: dict[str, ProjectRateInput] = {}
        self._customer_rate: ProjectRateInput = None
        self._domains: list[ProjectDomain] = []
        self.role_name_to_id = self._get_role_name_to_id()

    def set_name(self, name: str):
        self.project_name = name
        return self

    def set_media_type(self, media_type: "MediaType"):
        self.project_media_type = media_type
        return self

    def set_alignerr_role_rate(
        self,
        *,
        role_name: "AlignerrRole",
        rate: float,
        billing_mode: BillingMode,
        effective_since: datetime.datetime,
        effective_until: Optional[datetime.datetime] = None,
    ):
        if role_name.value not in self.role_name_to_id:
            raise ValueError(f"Role {role_name.value} not found")

        role_id = self.role_name_to_id[role_name.value]
        role_name = role_name.value

        # Convert datetime objects to ISO format strings
        effective_since_str = (
            effective_since.isoformat()
            if isinstance(effective_since, datetime.datetime)
            else effective_since
        )
        effective_until_str = (
            effective_until.isoformat()
            if isinstance(effective_until, datetime.datetime)
            else effective_until
        )

        self._alignerr_rates[role_name] = ProjectRateInput(
            rateForId=role_id,
            isBillRate=False,
            billingMode=billing_mode,
            rate=rate,
            effectiveSince=effective_since_str,
            effectiveUntil=effective_until_str,
        )
        return self

    def set_customer_rate(
        self,
        *,
        rate: float,
        billing_mode: BillingMode,
        effective_since: datetime.datetime,
        effective_until: Optional[datetime.datetime] = None,
    ):
        # Convert datetime objects to ISO format strings
        effective_since_str = (
            effective_since.isoformat()
            if isinstance(effective_since, datetime.datetime)
            else effective_since
        )
        effective_until_str = (
            effective_until.isoformat()
            if isinstance(effective_until, datetime.datetime)
            else effective_until
        )

        self._customer_rate = ProjectRateInput(
            rateForId="",  # Empty string for customer rate
            isBillRate=True,
            billingMode=billing_mode,
            rate=rate,
            effectiveSince=effective_since_str,
            effectiveUntil=effective_until_str,
        )
        return self

    def set_domains(self, domains: list[str]):
        for domain in domains:
            project_domain_page = ProjectDomain.search(
                self.client, search_by_name=domain
            )
            domain_result = project_domain_page.get_one()
            if domain_result is None:
                raise ValueError(f"Domain {domain} not found")
            self._domains.append(domain_result)
        return self

    def create(self, skip_validation: bool = False):
        if not skip_validation:
            self._validate()
        logger.info("Creating project")

        project_data = {
            "name": self.project_name,
            "media_type": self.project_media_type,
        }
        labelbox_project = self.client.create_project(**project_data)

        # Import here to avoid circular imports
        from labelbox.alignerr.alignerr_project import AlignerrProject

        alignerr_project = AlignerrProject(
            self.client, labelbox_project, _internal=True
        )

        self._create_rates(alignerr_project)
        self._create_domains(alignerr_project)

        return alignerr_project

    def _create_rates(self, alignerr_project: "AlignerrProject"):
        for alignerr_role, project_rate in self._alignerr_rates.items():
            logger.info(f"Setting project rate for {alignerr_role}")
            alignerr_project.set_project_rate(project_rate)

    def _create_domains(self, alignerr_project: "AlignerrProject"):
        if self._domains:
            logger.info(
                f"Setting domains: {[domain.name for domain in self._domains]}"
            )
            domain_ids = [domain.uid for domain in self._domains]
            ProjectDomain.connect_project_to_domains(
                client=self.client,
                project_id=alignerr_project.project.uid,
                domain_ids=domain_ids,
            )

    def _validate_alignerr_rates(self):
        # Import here to avoid circular imports
        from labelbox.alignerr.alignerr_project import AlignerrRole

        required_role_rates = set(
            [AlignerrRole.Labeler.value, AlignerrRole.Reviewer.value]
        )

        for role_name in self._alignerr_rates.keys():
            required_role_rates.remove(role_name)
        if len(required_role_rates) > 0:
            raise ValueError(
                f"Required role rates are not set: {required_role_rates}"
            )

    def _validate_customer_rate(self):
        if self._customer_rate is None:
            raise ValueError("Customer rate is not set")

    def _validate(self):
        self._validate_alignerr_rates()
        self._validate_customer_rate()

    def _get_role_name_to_id(self) -> dict[str, str]:
        roles = self.client.get_roles()
        return {role.name: role.uid for role in roles.values()}
