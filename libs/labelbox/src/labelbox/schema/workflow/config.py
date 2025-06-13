"""Configuration models for workflow initial nodes."""

from typing import Optional, Union, List
from pydantic import BaseModel, Field


class LabelingConfig(BaseModel):
    """Configuration for InitialLabeling node creation.

    Attributes:
        instructions: Task instructions for labelers
        max_contributions_per_user: Maximum contributions per user (null means infinite)
    """

    instructions: Optional[str] = Field(
        default=None, description="Task instructions for labelers"
    )
    max_contributions_per_user: Optional[int] = Field(
        default=None,
        description="Maximum contributions per user (null means infinite)",
        ge=0,
    )


class ReworkConfig(BaseModel):
    """Configuration for InitialRework node creation.

    Attributes:
        instructions: Task instructions for rework
        individual_assignment: User IDs for individual assignment
        max_contributions_per_user: Maximum contributions per user (null means infinite)
    """

    instructions: Optional[str] = Field(
        default=None, description="Task instructions for rework"
    )
    individual_assignment: Optional[Union[str, List[str]]] = Field(
        default=None, description="User IDs for individual assignment"
    )
    max_contributions_per_user: Optional[int] = Field(
        default=None,
        description="Maximum contributions per user (null means infinite)",
        ge=0,
    )
