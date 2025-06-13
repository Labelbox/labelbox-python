"""AutoQA node for automated quality assessment with pass/fail routing.

This module contains the AutoQANode class which performs automated quality assessment
using configured evaluators and score thresholds.
"""

from typing import Dict, List, Any, Optional, Literal
from pydantic import Field, model_validator, field_validator

from labelbox.schema.workflow.base import BaseWorkflowNode
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
)

# Constants for this module
DEFAULT_FILTER_LOGIC_AND: Literal["and"] = "and"


class AutoQANode(BaseWorkflowNode):
    """
    Automated Quality Assessment node with pass/fail routing.

    This node performs automated quality assessment using configured evaluators
    and score thresholds. Work that meets the quality criteria is routed to the
    "if" output (passed), while work that fails is routed to the "else" output.

    Attributes:
        label (str): Display name for the node (default: "Label Score (AutoQA)")
        filters (List[Dict[str, Any]]): Filter conditions for the AutoQA node
        filter_logic (str): Logic for combining filters ("and" or "or", default: "and")
        custom_fields (Dict[str, Any]): Additional custom configuration
        definition_id (WorkflowDefinitionId): Node type identifier (read-only)
        node_config (List[Dict[str, Any]]): API configuration for evaluator settings
        evaluator_id (Optional[str]): ID of the evaluator for AutoQA assessment
        scope (Optional[str]): Scope setting for AutoQA ("any" or "all")
        score_name (Optional[str]): Name of the score metric for evaluation
        score_threshold (Optional[float]): Threshold score for pass/fail determination

    Inputs:
        Default: Must have exactly one input connection

    Outputs:
        If: Route for work that passes quality assessment (score >= threshold)
        Else: Route for work that fails quality assessment (score < threshold)

    AutoQA Configuration:
        - evaluator_id: Specifies which evaluator to use for assessment
        - scope: Determines evaluation scope ("any" or "all" annotations)
        - score_name: The specific score metric to evaluate
        - score_threshold: Minimum score required to pass
        - Automatically syncs configuration with API format

    Validation:
        - Must have exactly one input connection
        - Both passed and failed outputs can be connected
        - AutoQA settings are automatically converted to API configuration
        - Evaluator and scoring parameters are validated

    Example:
        >>> autoqa = AutoQANode(
        ...     label="Quality Gate",
        ...     evaluator_id="evaluator-123",
        ...     scope="all",
        ...     score_name="accuracy",
        ...     score_threshold=0.85
        ... )
        >>> # Route high-quality work to done, low-quality to review
        >>> workflow.add_edge(autoqa, done_node, NodeOutput.If)
        >>> workflow.add_edge(autoqa, review_node, NodeOutput.Else)

    Quality Assessment:
        AutoQA nodes enable automated quality control by evaluating work
        against trained models or rule-based evaluators. This reduces manual
        review overhead while maintaining quality standards.

    Note:
        AutoQA requires properly configured evaluators and score thresholds.
        The evaluation results determine automatic routing without human intervention.
    """

    label: str = Field(default="Label Score (AutoQA)", max_length=50)
    filters: List[Dict[str, Any]] = Field(
        default_factory=lambda: [],
        description="Contains the filters for the AutoQA node",
    )
    filter_logic: Literal["and", "or"] = Field(
        default=DEFAULT_FILTER_LOGIC_AND, alias="filterLogic"
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=lambda: {},
        alias="customFields",
    )
    definition_id: WorkflowDefinitionId = Field(
        default=WorkflowDefinitionId.AutoQA,
        frozen=True,
        alias="definitionId",
    )
    node_config: List[Dict[str, Any]] = Field(
        default_factory=lambda: [],
        description="Contains evaluator_id, scope, score_name, score_threshold etc.",
        alias="config",
    )

    # AutoQA-specific fields
    evaluator_id: Optional[str] = Field(
        default=None,
        description="ID of the evaluator for AutoQA",
    )
    scope: Optional[str] = Field(
        default=None,
        description="Scope setting for AutoQA (any/all)",
    )
    score_name: Optional[str] = Field(
        default=None,
        description="Name of the score for AutoQA",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        description="Threshold score for AutoQA",
    )

    @model_validator(mode="after")
    def sync_autoqa_config_with_node_config(self) -> "AutoQANode":
        """Sync AutoQA-specific fields with node_config."""

        # Clear existing AutoQA config
        self.node_config = [
            config
            for config in self.node_config
            if config.get("field")
            not in ["evaluator_id", "scope", "score_name", "score_threshold"]
        ]

        # Add evaluator_id if present
        if self.evaluator_id is not None:
            self.node_config.append(
                {
                    "field": "evaluator_id",
                    "value": self.evaluator_id,
                    "metadata": None,
                }
            )

        # Add scope if present
        if self.scope is not None:
            self.node_config.append(
                {"field": "scope", "value": self.scope, "metadata": None}
            )

        # Add score_name if present
        if self.score_name is not None:
            self.node_config.append(
                {
                    "field": "score_name",
                    "value": self.score_name,
                    "metadata": None,
                }
            )

        # Add score_threshold if present
        if self.score_threshold is not None:
            self.node_config.append(
                {
                    "field": "score_threshold",
                    "value": self.score_threshold,
                    "metadata": None,
                }
            )

        return self

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v) -> List[str]:
        """Validate that AutoQA node has exactly one input."""
        if len(v) != 1:
            raise ValueError("AutoQA node must have exactly one input")
        return v

    @property
    def supported_outputs(self) -> List[NodeOutput]:
        """Returns the list of supported output types for this node."""
        return [NodeOutput.If, NodeOutput.Else]  # Passed (if) and Failed (else)
