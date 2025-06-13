"""
This module contains classes for managing project workflows in Labelbox.
It provides strongly-typed classes for nodes, edges, and workflow configuration.
"""

# Import all workflow classes to expose them at the package level
from labelbox.schema.workflow.enums import (
    WorkflowDefinitionId,
    NodeOutput,
    NodeInput,
    MatchFilters,
    Scope,
    FilterField,
    FilterOperator,
    IndividualAssignment,
)
from labelbox.schema.workflow.base import (
    BaseWorkflowNode,
    NodePosition,
)

# Import nodes from the nodes subdirectory
from labelbox.schema.workflow.nodes import (
    InitialLabelingNode,
    InitialReworkNode,
    ReviewNode,
    ReworkNode,
    DoneNode,
    CustomReworkNode,
    UnknownWorkflowNode,
    LogicNode,
    AutoQANode,
)

from labelbox.schema.workflow.edges import (
    WorkflowEdge,
    WorkflowEdgeFactory,
)
from labelbox.schema.workflow.graph import ProjectWorkflowGraph

# Import from monolithic workflow.py file
from labelbox.schema.workflow.workflow import (
    ProjectWorkflow,
    NodeType,
    InitialNodes,
)

# Import configuration classes
from labelbox.schema.workflow.config import LabelingConfig, ReworkConfig

# Import from monolithic project_filter.py file
from labelbox.schema.workflow.project_filter import (
    ProjectWorkflowFilter,
    labeled_by,
    annotation,
    dataset,
    issue_category,
    sample,
    metadata,
    model_prediction,
    natural_language,
    labeling_time,
    review_time,
    labeled_at,
    consensus_average,
    batch,
    feature_consensus_average,
    MetadataCondition,
    ModelPredictionCondition,
    m_condition,
    mp_condition,
    convert_to_api_format,
)

# Re-export key classes at the module level
__all__ = [
    # Core workflow components
    "WorkflowDefinitionId",
    "NodeOutput",
    "NodeInput",
    "MatchFilters",
    "Scope",
    "FilterField",
    "FilterOperator",
    "IndividualAssignment",
    "BaseWorkflowNode",
    "NodePosition",
    "InitialLabelingNode",
    "InitialReworkNode",
    "ReviewNode",
    "ReworkNode",
    "LogicNode",
    "DoneNode",
    "CustomReworkNode",
    "AutoQANode",
    "UnknownWorkflowNode",
    "WorkflowEdge",
    "WorkflowEdgeFactory",
    "ProjectWorkflow",
    "NodeType",
    "ProjectWorkflowGraph",
    "ProjectWorkflowFilter",
    # Workflow configuration
    "InitialNodes",
    "LabelingConfig",
    "ReworkConfig",
    # Filter field objects
    "labeled_by",
    "annotation",
    "dataset",
    "issue_category",
    # Filter construction functions
    "sample",
    "model_prediction",
    "natural_language",
    "labeled_at",
    "labeling_time",
    "review_time",
    "consensus_average",
    "batch",
    "feature_consensus_average",
    "metadata",
    "MetadataCondition",
    "ModelPredictionCondition",
    "m_condition",
    "mp_condition",
    # Utility functions
    "convert_to_api_format",
]

# Define a mapping of node types for workflow creation
NODE_TYPE_MAP = {
    WorkflowDefinitionId.InitialLabelingTask: InitialLabelingNode,
    WorkflowDefinitionId.InitialReworkTask: InitialReworkNode,
    WorkflowDefinitionId.ReviewTask: ReviewNode,
    WorkflowDefinitionId.SendToRework: ReworkNode,
    WorkflowDefinitionId.Logic: LogicNode,
    WorkflowDefinitionId.Done: DoneNode,
    WorkflowDefinitionId.CustomReworkTask: CustomReworkNode,
    WorkflowDefinitionId.AutoQA: AutoQANode,
    WorkflowDefinitionId.Unknown: UnknownWorkflowNode,
}
