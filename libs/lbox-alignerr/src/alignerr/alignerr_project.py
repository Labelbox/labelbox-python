from enum import Enum
from typing import TYPE_CHECKING, Optional

import logging

from alignerr.schema.project_rate import ProjectRateV2
from alignerr.schema.project_domain import ProjectDomain
from alignerr.schema.enchanced_resource_tags import (
    EnhancedResourceTag,
    ResourceTagType,
)
from alignerr.schema.project_boost_workforce import (
    ProjectBoostWorkforce,
)
from labelbox.pagination import PaginatedCollection
from labelbox.orm.model import Entity

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from labelbox import Client
    from labelbox.schema.project import Project
    from alignerr.schema.project_domain import ProjectDomain


class AlignerrRole(Enum):
    Labeler = "LABELER"
    Reviewer = "REVIEWER"
    Admin = "ADMIN"
    ProjectCoordinator = "PROJECT_COORDINATOR"
    AlignerrLabeler = "ALIGNERR_LABELER"
    EndLabellingRole = "ENDLABELLINGROLE"


class AlignerrProject:
    def __init__(self, client: "Client", project: "Project", _internal: bool = False):
        if not _internal:
            raise RuntimeError(
                "AlignerrProject cannot be initialized directly. "
                "Use AlignerrProjectBuilder or AlignerrProjectFactory to create instances."
            )
        self.client = client
        self.project = project

    @property
    def project(self) -> "Project":
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
            self.set_tags(current_tag_names, tag.type)

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
        self.set_tags(current_tag_names, tag.type)
        return self

    def get_project_owner(self) -> Optional[ProjectBoostWorkforce]:
        """Get the ProjectBoostWorkforce for this project.

        Returns:
            ProjectBoostWorkforce instance or None if not found
        """
        return ProjectBoostWorkforce.get_by_project_id(
            client=self.client, project_id=self.project.uid
        )

    def _get_user_labels(self, user_id: str):
        """Get all labels created by a user in this project.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of Label objects
            
        Raises:
            Exception: If labels cannot be retrieved
        """
        labels = list(self.project.labels(created_by=user_id))
        logger.info(
            "Found %d labels created by user %s in project %s",
            len(labels),
            user_id,
            self.project.uid
        )
        return labels

    def _create_trust_safety_case(self, user_id: str, event_metadata: dict) -> bool:
        """Create a Trust & Safety case for a user.
        
        Args:
            user_id: ID of the user being reported
            event_metadata: JSON metadata about the event
            
        Returns:
            True if case was created successfully
            
        Raises:
            Exception: If T&S case creation fails
        """
        mutation = """mutation CreateTrustAndSafetyCasePyApi(
            $subjectUserId: String!
            $eventType: CaseEventGqlType!
            $severity: CaseSeverityGqlType!
            $eventMetadata: Json!
        ) {
            createTrustAndSafetyCase(input: {
                subjectUserId: $subjectUserId
                eventType: $eventType
                severity: $severity
                eventMetadata: $eventMetadata
            }) {
                success
            }
        }"""
        
        params = {
            "subjectUserId": user_id,
            "eventType": "manual",
            "severity": "high",
            "eventMetadata": event_metadata,
        }
        
        result = self.client.execute(mutation, params)
        success = result["createTrustAndSafetyCase"]["success"]
        
        if success:
            logger.info(
                "Created T&S case for user %s in project %s",
                user_id,
                self.project.uid
            )
        
        return success

    def _remove_user_from_project(self, user_id: str) -> None:
        """Remove a user from this project.
        
        Args:
            user_id: ID of the user to remove
            
        Raises:
            ValueError: If user not found in project
            Exception: If removal fails
        """
        # Check if user is in project members
        user_found = False
        for member in self.project.members():
            if member.user().uid == user_id:
                user_found = True
                break
        
        if not user_found:
            logger.warning("User %s not found in project %s members", user_id, self.project.uid)
            raise ValueError(f"User {user_id} not found in project members")
        
        # Remove user using deleteProjectMemberships mutation
        result = self.client.delete_project_memberships(
            project_id=self.project.uid,
            user_ids=[user_id]
        )
        
        if not result.get("success"):
            error_message = result.get("errorMessage", "Unknown error")
            logger.error("Failed to remove user: %s", error_message)
            raise Exception(f"Failed to remove user: {error_message}")
        
        logger.info(
            "Removed user %s from project %s",
            user_id,
            self.project.uid
        )

    def _delete_user_labels(self, labels) -> int:
        """Delete a list of labels.
        
        Args:
            labels: List of Label objects to delete
            
        Returns:
            Number of labels deleted
            
        Raises:
            Exception: If deletion fails
        """
        if not labels:
            return 0
        
        Entity.Label.bulk_delete(labels)
        logger.info(
            "Deleted %d labels in project %s",
            len(labels),
            self.project.uid
        )
        return len(labels)

    def report_fraud(
        self,
        user_id: str,
        reason: str,
        custom_metadata: dict = None
    ) -> dict:
        """Report potential fraud by a user in this project.

        This method performs the following actions:
        1. Gets all labels created by the user in this project
        2. Creates a Trust & Safety case for the user (MANUAL event type, HIGH severity)
        3. Removes the user from the project (prevents creating more labels)
        4. Deletes all the user's labels
        
        Args:
            user_id (str): The ID of the user to report for fraud.
            reason (str): Reason for reporting fraud (e.g., "Spam labels", "Low quality work").
            custom_metadata (dict, optional): Additional metadata to include in the T&S case.
                Will be merged with automatic metadata (project_id, reason, label_count, label_ids).
            
        Returns:
            dict: A dictionary containing:
                - ts_case_id: Status of T&S case creation ("created" if successful)
                - labels_found: Number of labels found by the user
                - user_removed: Whether the user was successfully removed
                - labels_deleted: Number of labels deleted
                - error: Any error message if any step failed
                
        Example:
            >>> from alignerr import AlignerrWorkspace
            >>> from labelbox import Client
            >>> 
            >>> client = Client(api_key="YOUR_API_KEY")
            >>> workspace = AlignerrWorkspace.from_labelbox(client)
            >>> project = workspace.project_builder().from_existing(project_id)
            >>> 
            >>> # Report fraud with reason
            >>> result = project.report_fraud(user_id, reason="Spam labels detected")
            >>> print(f"Removed user: {result['user_removed']}, Deleted {result['labels_deleted']} labels")
            >>> 
            >>> # With additional custom metadata
            >>> result = project.report_fraud(
            >>>     user_id,
            >>>     reason="Production quality issues",
            >>>     custom_metadata={"ticket_id": "TICKET-123", "reviewer": "john@example.com"}
            >>> )
        """
        result = {
            "ts_case_id": None,
            "labels_found": 0,
            "user_removed": False,
            "labels_deleted": 0,
            "error": None,
        }
        
        # Step 1: Get all labels cteated by this user in this project
        try:
            labels_to_delete = self._get_user_labels(user_id)
            result["labels_found"] = len(labels_to_delete)
        except Exception as e:
            logger.error("Failed to get labels: %s", str(e))
            result["error"] = f"Failed to get labels: {str(e)}"
            return result
        
        # Step 2: Create T&S case with label information
        try:
            event_metadata = {
                "project_id": self.project.uid,
                "reason": reason,
                "label_count": len(labels_to_delete),
                "label_ids": [label.uid for label in labels_to_delete],
            }
            if custom_metadata:
                event_metadata.update(custom_metadata)
            
            ts_case_created = self._create_trust_safety_case(user_id, event_metadata)
            if ts_case_created:
                result["ts_case_id"] = "created"
        except Exception as e:
            logger.error("Failed to create T&S case: %s", str(e))
            result["error"] = f"Failed to create T&S case: {str(e)}"
            return result
        
        # Step 3: Remove user from project (prevent creating more labels)
        try:
            self._remove_user_from_project(user_id)
            result["user_removed"] = True
        except Exception as e:
            logger.error("Failed to remove user from project: %s", str(e))
            result["error"] = f"Failed to remove user: {str(e)}"
            return result
        
        # Step 4: Delete all labels by this user
        try:
            result["labels_deleted"] = self._delete_user_labels(labels_to_delete)
        except Exception as e:
            logger.error("Failed to delete labels: %s", str(e))
            result["error"] = f"Failed to delete labels: {str(e)}"
            return result
        
        return result


class AlignerrWorkspace:
    def __init__(self, client: "Client"):
        self.client = client

    def project_builder(self):
        from alignerr.alignerr_project_builder import (
            AlignerrProjectBuilder,
        )

        return AlignerrProjectBuilder(self.client)

    def project_prototype(self):
        from alignerr.alignerr_project_factory import (
            AlignerrProjectFactory,
        )

        return AlignerrProjectFactory(self.client)

    @classmethod
    def from_labelbox(cls, client: "Client") -> "AlignerrWorkspace":
        return cls(client)
