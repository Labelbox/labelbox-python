from enum import Enum
from typing import Optional
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Relationship, Field
from pydantic import BaseModel


class ProjectBoostWorkforceStatus(Enum):
    """Enum for ProjectBoostWorkforce status."""

    SET_UP = "SET_UP"
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    CALIBRATION = "CALIBRATION"
    PRODUCTION = "PRODUCTION"
    COMPLETE = "COMPLETE"
    PAUSED = "PAUSED"


class ProjectBoostType(Enum):
    """Enum for ProjectBoost type."""

    SELF_SERVE = "SELF_SERVE"
    MANAGED = "MANAGED"


class ProjectDifficulty(Enum):
    """Enum for project difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BillingMode(Enum):
    """Enum for billing modes."""

    BY_TASK = "BY_TASK"
    BY_HOUR = "BY_HOUR"
    BY_TASK_PER_TURN = "BY_TASK_PER_TURN"


class UpsertProjectBoostWorkforceInput(BaseModel):
    """Input for upserting a ProjectBoostWorkforce."""

    projectId: str


class UpdateProjectBoostWorkforceStatusInput(BaseModel):
    """Input for updating ProjectBoostWorkforce status."""

    projectId: str
    status: ProjectBoostWorkforceStatus


class UpdateProjectBoostWorkforceCountryMultiplierInput(BaseModel):
    """Input for updating country rate multipliers."""

    projectId: str
    disabledCountryRateMultipliers: bool


class UpdateProjectBoostWorkforceBillingModeInput(BaseModel):
    """Input for updating billing mode."""

    projectId: str
    billingMode: BillingMode
    customerBillingMode: Optional[BillingMode] = None


class ValidateAndRequestProjectBoostWorkforceInput(BaseModel):
    """Input for validating and requesting ProjectBoostWorkforce."""

    projectId: str


class UpdateProjectBoostWorkforceInput(BaseModel):
    """Input for updating ProjectBoostWorkforce."""

    projectId: str
    status: Optional[ProjectBoostWorkforceStatus] = None
    calibrationDatarows: Optional[int] = None
    reworkThreshold: Optional[float] = None
    jiraTicketUrl: Optional[str] = None
    slackChannelUrl: Optional[str] = None
    sampleVideoUrl: Optional[str] = None
    projectDifficulty: Optional[ProjectDifficulty] = None
    estimatedTimePerLabel: Optional[float] = None
    projectDescription: Optional[str] = None
    pilotStatus: Optional[bool] = None
    discordLandingChannelId: Optional[str] = None
    discordLabelerRoleId: Optional[str] = None
    discordGuildId: Optional[str] = None
    discordReviewerChannelId: Optional[str] = None
    discordReviewerRoleId: Optional[str] = None
    projectOwnerUserId: Optional[str] = None


class FindProjectBoostWorkforceInput(BaseModel):
    """Input for finding ProjectBoostWorkforce."""

    projectId: str


class ProjectBoostWorkforceResult(BaseModel):
    """Result model for ProjectBoostWorkforce operations."""

    success: bool


class ProjectBoostWorkforceStatusHistoryFields(BaseModel):
    """Model for ProjectBoostWorkforce status history fields."""

    id: str
    projectId: str
    updatedAt: str
    updatedById: str
    status: ProjectBoostWorkforceStatus


class ProjectBoostWorkforce(DbObject):
    """A ProjectBoostWorkforce represents workforce management for a project."""

    # Relationships
    projectOwner = Relationship.ToOne("User", False)

    # Fields matching the GraphQL schema
    id = Field.String("id")
    projectId = Field.String("projectId")
    createdAt = Field.DateTime("createdAt")
    updatedAt = Field.DateTime("updatedAt")
    createdById = Field.String("createdById")
    createdByEmail = Field.String("createdByEmail")
    updatedById = Field.String("updatedById")
    status = Field.Enum(ProjectBoostWorkforceStatus, "status")
    calibrationDatarows = Field.Int("calibrationDatarows")
    reworkThreshold = Field.Float("reworkThreshold")
    jiraTicketUrl = Field.String("jiraTicketUrl")
    slackChannelUrl = Field.String("slackChannelUrl")
    pilotStatus = Field.Boolean("pilotStatus")
    discourseCategoryUrl = Field.String("discourseCategoryUrl")
    sampleVideoUrl = Field.String("sampleVideoUrl")
    projectDifficulty = Field.Enum(ProjectDifficulty, "projectDifficulty")
    projectDescription = Field.String("projectDescription")
    estimatedTimePerLabel = Field.Float("estimatedTimePerLabel")
    disabledCountryRateMultipliers = Field.Boolean(
        "disabledCountryRateMultipliers"
    )
    billingMode = Field.Enum(BillingMode, "billingMode")
    customerBillingMode = Field.Enum(BillingMode, "customerBillingMode")
    type = Field.Enum(ProjectBoostType, "type")
    isPaused = Field.Boolean("isPaused")
    isAnnotatingPausedForUser = Field.Boolean("isAnnotatingPausedForUser")
    isPayPerTaskEnabled = Field.Boolean("isPayPerTaskEnabled")
    codeId = Field.String("codeId")
    projectOwnerUserId = Field.String("projectOwnerUserId")

    @classmethod
    def get_by_project_id(
        cls, client, project_id: str
    ) -> Optional["ProjectBoostWorkforce"]:
        """Get ProjectBoostWorkforce by project ID.

        Args:
            client: Labelbox client instance
            project_id: ID of the project

        Returns:
            ProjectBoostWorkforce instance or None if not found
        """
        input_data = FindProjectBoostWorkforceInput(projectId=project_id)

        query_str = """
        query GetProjectBoostWorkforcePyApi($data: FindProjectBoostWorkforceInput!) {
            projectBoostWorkforce(data: $data) {
                id
                projectId
                createdAt
                updatedAt
                createdById
                createdByEmail
                updatedById
                status
                calibrationDatarows
                reworkThreshold
                jiraTicketUrl
                slackChannelUrl
                pilotStatus
                discourseCategoryUrl
                sampleVideoUrl
                projectDifficulty
                projectDescription
                estimatedTimePerLabel
                disabledCountryRateMultipliers
                billingMode
                customerBillingMode
                type
                isPaused
                isAnnotatingPausedForUser
                isPayPerTaskEnabled
                codeId
                projectOwnerUserId
                projectOwner {
                    id
                    email
                    name
                }
            }
        }"""

        result = client.execute(query_str, {"data": input_data.model_dump()})
        workforce_data = result.get("projectBoostWorkforce")

        if not workforce_data:
            return None

        return cls(client, workforce_data)

    @classmethod
    def update(
        cls, client, update_input: UpdateProjectBoostWorkforceInput
    ) -> ProjectBoostWorkforceResult:
        """Update ProjectBoostWorkforce with various fields.

        Args:
            client: Labelbox client instance
            update_input: UpdateProjectBoostWorkforceInput with fields to update

        Returns:
            ProjectBoostWorkforceResult indicating success
        """
        mutation_str = """
        mutation UpdateProjectBoostWorkforcePyApi($data: UpdateProjectBoostWorkforceInput!) {
            updateProjectBoostWorkforce(data: $data) {
                success
            }
        }"""

        result = client.execute(
            mutation_str, {"data": update_input.model_dump()}
        )
        return ProjectBoostWorkforceResult(
            **result["updateProjectBoostWorkforce"]
        )

    @classmethod
    def set_project_owner(
        cls, client, project_id: str, project_owner_user_id: str
    ) -> ProjectBoostWorkforceResult:
        """Set the project owner for ProjectBoostWorkforce.

        Args:
            client: Labelbox client instance
            project_id: ID of the project
            project_owner_user_id: ID of the user to set as project owner

        Returns:
            ProjectBoostWorkforceResult indicating success
        """
        update_input = UpdateProjectBoostWorkforceInput(
            projectId=project_id, projectOwnerUserId=project_owner_user_id
        )

        return cls.update(client, update_input)
