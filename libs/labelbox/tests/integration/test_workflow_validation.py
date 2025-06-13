"""
Tests for workflow validation and error handling.

Tests that the new validation prevents invalid workflow states and provides clear error messages.
"""

import pytest
from labelbox.schema.workflow import NodeType, LabelingConfig, ReworkConfig
from labelbox.schema.media_type import MediaType


def test_cannot_create_initial_nodes_via_add_node(client):
    """Test that creating initial nodes via add_node is blocked."""
    project = client.create_project(
        name="Test Validation", media_type=MediaType.Image
    )

    try:
        workflow = project.get_workflow()
        initial_nodes = workflow.reset_to_initial_nodes()

        # Should fail when trying to create additional initial nodes
        with pytest.raises(
            ValueError,
            match="Cannot create initial_labeling_task nodes via add_node",
        ):
            workflow.add_node(type=NodeType.InitialLabeling)

        with pytest.raises(
            ValueError,
            match="Cannot create initial_rework_task nodes via add_node",
        ):
            workflow.add_node(type=NodeType.InitialRework)

    finally:
        project.delete()


def test_cannot_delete_initial_nodes(client):
    """Test that deleting initial nodes is blocked."""
    project = client.create_project(
        name="Test Validation", media_type=MediaType.Image
    )

    try:
        workflow = project.get_workflow()
        initial_nodes = workflow.reset_to_initial_nodes()

        # Should fail when trying to delete initial nodes
        with pytest.raises(
            ValueError, match="Cannot delete InitialLabeling node"
        ):
            workflow.delete_nodes([initial_nodes.labeling])

        with pytest.raises(
            ValueError, match="Cannot delete InitialRework node"
        ):
            workflow.delete_nodes([initial_nodes.rework])

    finally:
        project.delete()


def test_valid_workflow_with_configs(client):
    """Test that workflows with proper configurations work correctly."""
    project = client.create_project(
        name="Test Validation", media_type=MediaType.Image
    )

    try:
        workflow = project.get_workflow()

        # Should work with configuration
        initial_nodes = workflow.reset_to_initial_nodes(
            labeling_config=LabelingConfig(
                instructions="Label carefully", max_contributions_per_user=5
            ),
            rework_config=ReworkConfig(
                instructions="Fix the issues",
                individual_assignment=["user-123"],
                max_contributions_per_user=3,
            ),
        )

        # Verify nodes were created with correct config
        assert initial_nodes.labeling.instructions == "Label carefully"
        assert initial_nodes.labeling.max_contributions_per_user == 5
        assert initial_nodes.rework.instructions == "Fix the issues"
        assert initial_nodes.rework.individual_assignment == ["user-123"]
        assert initial_nodes.rework.max_contributions_per_user == 3

        # Should be able to create other node types
        done = workflow.add_node(type=NodeType.Done)
        workflow.add_edge(initial_nodes.labeling, done)
        workflow.add_edge(initial_nodes.rework, done)

        # Should validate and update successfully
        workflow.update_config()

    finally:
        project.delete()


def test_empty_workflow_validation_fails(client):
    """Test that workflows with missing initial nodes fail validation."""
    project = client.create_project(
        name="Test Validation", media_type=MediaType.Image
    )

    try:
        workflow = project.get_workflow()

        # Manually create invalid state for testing (bypassing public API)
        workflow.config = {"nodes": [], "edges": []}
        workflow._nodes_cache = None
        workflow._edges_cache = None

        # Should fail validation
        with pytest.raises(
            ValueError, match="Use workflow.reset_to_initial_nodes"
        ):
            workflow.update_config()

    finally:
        project.delete()
