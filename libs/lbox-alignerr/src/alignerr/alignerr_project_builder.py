from enum import Enum
from typing import TYPE_CHECKING, Optional, Union, List
import logging

from alignerr.alignerr_project import PAY_BY_ROLE_REMOVED_MSG
from alignerr.schema.project_domain import ProjectDomain
from alignerr.schema.enchanced_resource_tags import (
    EnhancedResourceTag,
    ResourceTagType,
)
from alignerr.schema.project_boost_workforce import (
    ProjectBoostWorkforce,
)
from labelbox.schema.media_type import MediaType

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """Enum for validation types that can be selectively skipped."""

    ALIGNERR_RATE = "AlignerrRate"
    CUSTOMER_RATE = "CustomerRate"
    PROJECT_OWNER = "ProjectOwner"


if TYPE_CHECKING:
    from labelbox import Client
    from alignerr.alignerr_project import AlignerrProject


class AlignerrProjectBuilder:
    def __init__(self, client: "Client"):
        self.client = client
        self._domains: list[ProjectDomain] = []
        self._enhanced_resource_tags: list[EnhancedResourceTag] = []
        self._project_owner_email: Optional[str] = None

    def set_name(self, name: str):
        self.project_name = name
        return self

    def set_media_type(self, media_type: "MediaType"):
        self.project_media_type = media_type
        return self

    def set_alignerr_role_rate(self, *args, **kwargs):
        raise NotImplementedError(PAY_BY_ROLE_REMOVED_MSG)

    def set_customer_rate(self, *args, **kwargs):
        raise NotImplementedError(PAY_BY_ROLE_REMOVED_MSG)

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

    def set_tags(self, tag_texts: list[str], tag_type: ResourceTagType):
        """Set enhanced resource tags for the project.

        Args:
            tag_texts: List of tag text values to search for and attach
            tag_type: Type filter for searching tags

        Returns:
            Self for method chaining
        """
        for tag_text in tag_texts:
            # Search for existing tags by text
            existing_tags = EnhancedResourceTag.search_by_text(
                self.client, search_text=tag_text, tag_type=tag_type
            )

            if existing_tags:
                # Use the first matching tag
                self._enhanced_resource_tags.append(existing_tags[0])
            else:
                # Create new tag if not found
                new_tag = EnhancedResourceTag.create(
                    self.client,
                    text=tag_text,
                    color="#007bff",  # Default blue color
                    tag_type=tag_type,
                )
                self._enhanced_resource_tags.append(new_tag)
        return self

    def set_project_owner(self, project_owner_email: str):
        """Set the project owner for the ProjectBoostWorkforce.

        Args:
            project_owner_email: Email of the user to set as project owner

        Returns:
            Self for method chaining
        """
        self._project_owner_email = project_owner_email
        return self

    def create(self, skip_validation: Union[bool, List[ValidationType]] = False):
        if not skip_validation:
            self._validate()
        elif isinstance(skip_validation, list):
            self._validate_selective(skip_validation)
        logger.info("Creating project")

        project_data = {
            "name": self.project_name,
            "media_type": self.project_media_type,
        }
        labelbox_project = self.client.create_project(**project_data)

        # Import here to avoid circular imports
        from alignerr.alignerr_project import AlignerrProject

        alignerr_project = AlignerrProject(
            self.client, labelbox_project, _internal=True
        )

        self._create_domains(alignerr_project)
        self._create_resource_tags(alignerr_project)
        self._create_project_owner(alignerr_project)

        return alignerr_project

    def _create_domains(self, alignerr_project: "AlignerrProject"):
        if self._domains:
            logger.info(f"Setting domains: {[domain.name for domain in self._domains]}")
            domain_ids = [domain.uid for domain in self._domains]
            ProjectDomain.connect_project_to_domains(
                client=self.client,
                project_id=alignerr_project.project.uid,
                domain_ids=domain_ids,
            )

    def _create_resource_tags(self, alignerr_project: "AlignerrProject"):
        if self._enhanced_resource_tags:
            logger.info(
                f"Setting enhanced resource tags: {[tag.text for tag in self._enhanced_resource_tags]}"
            )
            # Group tags by type and set them accordingly
            tags_by_type: dict[ResourceTagType, list[str]] = {}
            for tag in self._enhanced_resource_tags:
                tag_type = tag.type
                if tag_type not in tags_by_type:
                    tags_by_type[tag_type] = []
                tags_by_type[tag_type].append(tag.text)

            # Set tags for each type
            for tag_type_str, tag_names in tags_by_type.items():
                # Convert string back to enum
                tag_type_enum = ResourceTagType(tag_type_str)
                alignerr_project.set_tags(tag_names, tag_type_enum)

    def _create_project_owner(self, alignerr_project: "AlignerrProject"):
        if self._project_owner_email:
            logger.info(f"Setting project owner: {self._project_owner_email}")

            # Find user by email in the organization
            user_id = self._find_user_by_email(self._project_owner_email)
            if not user_id:
                current_org = self.client.get_organization()
                raise ValueError(
                    f"User with email {self._project_owner_email} not found in organization {current_org.uid}"
                )

            ProjectBoostWorkforce.set_project_owner(
                client=self.client,
                project_id=alignerr_project.project.uid,
                project_owner_user_id=user_id,
            )

    def _validate_project_owner(self):
        if self._project_owner_email is None:
            raise ValueError("Project owner is not set")

    def _validate(self):
        self._validate_project_owner()

    def _validate_selective(self, skip_validations: List[ValidationType]):
        """Run validations selectively, skipping those in the provided list.

        Args:
            skip_validations: List of ValidationType enums to skip
        """
        # ALIGNERR_RATE / CUSTOMER_RATE are retained for callers that still pass them
        # in skip_validation lists; rate validation itself has been removed.
        if ValidationType.PROJECT_OWNER not in skip_validations:
            self._validate_project_owner()

    def _find_user_by_email(self, email: str) -> Optional[str]:
        """Find user ID by email in the organization.

        Args:
            email: Email address to search for

        Returns:
            User ID if found, None otherwise
        """
        try:
            # Import here to avoid circular imports
            from labelbox.schema.user import User

            # Get the current organization
            current_org = self.client.get_organization()

            # Use client.get_users with where clause to find user by email
            users = self.client.get_users(where=User.email == email)

            # Get the first matching user and verify they belong to the same organization
            user = next(users, None)
            if user and user.organization().uid == current_org.uid:
                return user.uid
            else:
                logger.warning(
                    f"User with email {email} not found in organization {current_org.uid}"
                )
                return None

        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None
