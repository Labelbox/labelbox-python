from dataclasses import dataclass

from labelbox.schema.workflow.enums import WorkflowDefinitionId
from labelbox.schema.workflow.graph import ProjectWorkflowGraph
from labelbox.schema.workflow.workflow_utils import WorkflowValidator


@dataclass(frozen=True)
class _Node:
    id: str
    definition_id: WorkflowDefinitionId


def test_validate_node_connections_allows_multiple_incoming_from_non_initial_nodes():
    """
    Regression test: nodes may have multiple incoming connections from any nodes.

    Historically validation required that if a node had >1 predecessors, they all had
    to be initial nodes. Workflow Management now allows multi-input nodes from any
    nodes, so this must not error.
    """
    initial_labeling = _Node(
        id="initial_labeling",
        definition_id=WorkflowDefinitionId.InitialLabelingTask,
    )
    initial_rework = _Node(
        id="initial_rework",
        definition_id=WorkflowDefinitionId.InitialReworkTask,
    )
    logic = _Node(id="logic", definition_id=WorkflowDefinitionId.Logic)
    review = _Node(id="review", definition_id=WorkflowDefinitionId.ReviewTask)
    done = _Node(id="done", definition_id=WorkflowDefinitionId.Done)

    nodes = [initial_labeling, initial_rework, logic, review, done]

    graph = ProjectWorkflowGraph()
    graph.add_edge(initial_labeling.id, logic.id)
    graph.add_edge(logic.id, review.id)
    graph.add_edge(initial_rework.id, review.id)
    graph.add_edge(review.id, done.id)

    errors = WorkflowValidator.validate_node_connections(nodes, graph)
    assert errors == []


def test_validate_node_connections_still_flags_missing_incoming_connections():
    """Non-initial nodes must still have at least one incoming connection."""
    initial_labeling = _Node(
        id="initial_labeling",
        definition_id=WorkflowDefinitionId.InitialLabelingTask,
    )
    review = _Node(id="review", definition_id=WorkflowDefinitionId.ReviewTask)
    done = _Node(id="done", definition_id=WorkflowDefinitionId.Done)

    nodes = [initial_labeling, review, done]
    graph = ProjectWorkflowGraph()
    graph.add_edge(initial_labeling.id, done.id)

    errors = WorkflowValidator.validate_node_connections(nodes, graph)
    assert any(
        e.get("node_id") == review.id
        and e.get("reason") == "has no incoming connections"
        for e in errors
    )
