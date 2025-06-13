"""Enums for Project Workflows in Labelbox.

This module defines all the enumeration types used in project workflows,
including node types, filter options, and output types.
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class IndividualAssignment(Enum):
    """Special individual assignment targets for workflow nodes.

    These values are used to specify special assignment targets
    like the original label creator for review workflows.
    """

    LabelCreator = "LABEL_CREATOR"


class WorkflowDefinitionId(Enum):
    """Types of workflow nodes supported in the Labelbox platform.

    Each enum value corresponds to a specific type of workflow node
    that can be used in project workflows.
    """

    InitialLabelingTask = "initial_labeling_task"
    InitialReworkTask = "initial_rework_task"
    ReviewTask = "review_task"
    SendToRework = "send_to_rework"  # Maps to ReworkNode in UI
    Logic = "logic"
    Done = "done"
    CustomReworkTask = "custom_rework_task"
    AutoQA = "auto_qa"
    Unknown = "unknown"  # For unrecognized node types from API


class NodeType(Enum):
    """Node types available for workflow creation.

    These values are used when programmatically creating new workflow nodes.
    """

    InitialLabeling = "initial_labeling_task"
    InitialRework = "initial_rework_task"
    Review = "review_task"
    Rework = "send_to_rework"
    Logic = "logic"
    Done = "done"
    CustomRework = "custom_rework_task"
    AutoQA = "auto_qa"


class NodeOutput(str, Enum):
    """Available output types for workflow nodes.

    Defines the different output handles that nodes can have for
    connecting to other nodes in the workflow.
    """

    If = "if"
    Else = "else"
    Approved = "if"  # Alias for review node approved output
    Rejected = "else"  # Alias for review node rejected output
    Default = "out"


class NodeInput(str, Enum):
    """Available input types for workflow nodes.

    Defines the different input handles that nodes can have for
    receiving connections from other nodes.
    """

    Default = "in"


class MatchFilters(str, Enum):
    """Available match filter options for LogicNode.

    Determines how multiple filters in a LogicNode are combined.
    """

    Any = "any"  # Maps to filter_logic "or" - matches if any filter passes
    All = "all"  # Maps to filter_logic "and" - matches if all filters pass


class Scope(str, Enum):
    """Available scope options for AutoQANode.

    Determines how AutoQA evaluation is applied to annotations.
    """

    Any = "any"  # Passes if any annotation meets the criteria
    All = "all"  # Passes only if all annotations meet the criteria


class FilterField(str, Enum):
    """Available filter fields for LogicNode filters.

    Defines all the fields that can be used in workflow logic filters
    to create conditional routing rules.
    """

    # User and creation filters
    LabeledBy = "CreatedBy"  # Maps to backend CreatedBy field

    # Annotation and content filters
    Annotation = "Annotation"
    LabeledAt = "LabeledAt"
    Sample = "Sample"

    # Quality and consensus filters
    ConsensusAverage = "ConsensusAverage"
    FeatureConsensusAverage = "FeatureConsensusAverage"

    # Organization filters
    Dataset = "Dataset"
    IssueCategory = "IssueCategory"
    Batch = "Batch"

    # Custom and advanced filters
    Metadata = "Metadata"
    ModelPrediction = "ModelPrediction"

    # Performance filters
    LabelingTime = "LabelingTime"
    ReviewTime = "ReviewTime"

    # Search filters
    NlSearch = "NlSearch"


class FilterOperator(str, Enum):
    """Available filter operators for LogicNode filters.

    Defines all the operators that can be used with filter fields
    to create filter conditions.
    """

    # Basic equality operators
    Is = "is"
    IsNot = "is not"

    # Text search operators
    Contains = "contains"
    DoesNotContain = "does not contain"

    # List membership operators
    In = "in"
    NotIn = "not in"

    # Comparison operators (using server-expected format)
    GreaterThan = "greater_than"
    LessThan = "less_than"
    GreaterThanOrEqual = "greater_than_or_equal"
    LessThanOrEqual = "less_than_or_equal"

    # Range operators
    Between = "between"
