from enum import Enum
from typing import Optional
from labelbox.orm.db_object import DbObject, Deletable
from labelbox.orm.model import Relationship, Field
from pydantic import BaseModel, model_validator


class BillingMode(Enum):
    BY_TASK = "BY_TASK"
    BY_HOUR = "BY_HOUR"
    BY_TASK_PER_TURN = "BY_TASK_PER_TURN"
    BY_ACCEPTED_TASK = "BY_ACCEPTED_TASK"


class ProjectRateInput(BaseModel):
    rateForId: str
    isBillRate: bool
    billingMode: BillingMode
    rate: float
    effectiveSince: str  # DateTime as string
    effectiveUntil: Optional[str] = None  # Optional DateTime as string

    @model_validator(mode="after")
    def validate_fields(self):
        if self.rate < 0:
            raise ValueError("Rate must be greater than or equal to 0")

        if self.isBillRate and self.rateForId != "":
            raise ValueError(
                "isBillRate indicates that this is a customer bill rate. rateForId must be empty if isBillRate is true"
            )

        if not self.isBillRate and self.rateForId == "":
            raise ValueError(
                "rateForId must be set to the id of the Alignerr Role"
            )

        return self


class ProjectRateV2(DbObject, Deletable):
    # Relationships
    userRole = Relationship.ToOne("UserRole", False)
    updatedBy = Relationship.ToOne("User", False)

    # Fields matching the GraphQL schema
    isBillRate = Field.Boolean("isBillRate")
    billingMode = Field.Enum(BillingMode, "billingMode")
    rate = Field.Float("rate")
    createdAt = Field.DateTime("createdAt")
    updatedAt = Field.DateTime("updatedAt")
    effectiveSince = Field.DateTime("effectiveSince")
    effectiveUntil = Field.DateTime("effectiveUntil")

    @classmethod
    def get_by_project_id(
        cls, client, project_id: str
    ) -> list["ProjectRateV2"]:
        query_str = """
        query GetAllProjectRatesPyApi($projectId: ID!) {
            project(where: { id: $projectId }) {
                id
                ratesV2 {
                    id
                    userRole {
                        id
                        name
                    }
                    isBillRate
                    billingMode
                    rate
                    effectiveSince
                    effectiveUntil
                    createdAt
                    updatedAt
                    updatedBy {
                        id
                        email
                        name
                    }
                }
            }
        }
        """
        result = client.execute(query_str, {"projectId": project_id})
        rates_data = result["project"]["ratesV2"]

        if not rates_data:
            return []

        # Return all rates as ProjectRateV2 objects
        return [cls(client, rate_data) for rate_data in rates_data]

    @classmethod
    def set_project_rate(
        cls, client, project_id: str, project_rate_input: ProjectRateInput
    ):
        mutation_str = """mutation SetProjectRateV2PyApi($input: SetProjectRateV2Input!) {
                setProjectRateV2(input: $input) {
                    success
                }
        }"""

        params = {
            "projectId": project_id,
            "input": {
                "projectId": project_id,
                "userRoleId": project_rate_input.rateForId,
                "isBillRate": project_rate_input.isBillRate,
                "billingMode": project_rate_input.billingMode.value
                if hasattr(project_rate_input.billingMode, "value")
                else project_rate_input.billingMode,
                "rate": project_rate_input.rate,
                "effectiveSince": project_rate_input.effectiveSince,
                "effectiveUntil": project_rate_input.effectiveUntil,
            },
        }

        result = client.execute(mutation_str, params)

        return result["setProjectRateV2"]["success"]
