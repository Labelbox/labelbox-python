"""
Integration tests for Workflow functionality.

Tests the following workflow operations:
- Creating workflows with different node types
- Updating workflows with configuration changes
- Copying workflows between projects
- LogicNode filter operations (add/remove/update)
- Node removal operations with validation
- Production-like workflow configurations
"""

import pytest
import uuid
from datetime import datetime
from labelbox.schema.workflow import (
    NodeOutput,
    NodeType,
    MatchFilters,
    ProjectWorkflowFilter,
    WorkflowDefinitionId,
    FilterField,
    LabelingConfig,
    labeled_by,
    dataset,
    natural_language,
    labeling_time,
    metadata,
    convert_to_api_format,
    model_prediction,
    mp_condition,
    m_condition,
    annotation,
    sample,
    consensus_average,
    review_time,
    labeled_at,
    ReworkConfig,
)
from labelbox.schema.media_type import MediaType


@pytest.fixture
def test_projects(client):
    """Create two projects for workflow testing."""
    source_name = f"Workflow Test Source {uuid.uuid4()}"
    source_project = client.create_project(
        name=source_name, media_type=MediaType.Image
    )

    target_name = f"Workflow Test Target {uuid.uuid4()}"
    target_project = client.create_project(
        name=target_name, media_type=MediaType.Image
    )

    yield source_project, target_project

    source_project.delete()
    target_project.delete()


def test_workflow_creation(client, test_projects):
    """Test creating a new workflow from scratch."""
    source_project, _ = test_projects

    workflow = source_project.get_workflow()

    # Create workflow with required initial nodes
    initial_nodes = workflow.reset_to_initial_nodes(
        labeling_config=LabelingConfig(instructions="Start labeling here")
    )

    review_node = workflow.add_node(type=NodeType.Review, name="Review Task")
    done_node = workflow.add_node(type=NodeType.Done, name="Done")

    # Connect both initial nodes to review node
    workflow.add_edge(initial_nodes.labeling, review_node)
    workflow.add_edge(initial_nodes.rework, review_node)
    workflow.add_edge(review_node, done_node, NodeOutput.Approved)

    workflow.update_config(reposition=False)

    updated_workflow = source_project.get_workflow()
    nodes = updated_workflow.get_nodes()
    edges = updated_workflow.get_edges()

    assert (
        len(nodes) == 4
    ), "Should have 4 nodes (2 initial + 1 review + 1 done)"
    assert len(edges) == 3, "Should have 3 edges"

    node_types = [node.definition_id for node in nodes]
    assert WorkflowDefinitionId.InitialLabelingTask in node_types
    assert WorkflowDefinitionId.InitialReworkTask in node_types
    assert WorkflowDefinitionId.ReviewTask in node_types
    assert WorkflowDefinitionId.Done in node_types


def test_workflow_creation_simple(client):
    """Test creating a simple workflow with the working pattern."""
    # Create a new project for this test
    project_name = f"Simple Workflow Test {uuid.uuid4()}"
    project = client.create_project(
        name=project_name, media_type=MediaType.Image
    )

    try:
        # Get or create workflow
        workflow = project.get_workflow()

        # Create workflow with required initial nodes
        initial_nodes = workflow.reset_to_initial_nodes(
            labeling_config=LabelingConfig(
                instructions="This is the entry point"
            )
        )

        review = workflow.add_node(
            type=NodeType.Review, name="Test review task"
        )

        # Create done nodes
        done = workflow.add_node(type=NodeType.Done)

        # Create send to rework node
        rework = workflow.add_node(type=NodeType.Rework)

        # Connect nodes using NodeOutput enum
        workflow.add_edge(initial_nodes.labeling, review)
        workflow.add_edge(initial_nodes.rework, review)
        workflow.add_edge(review, rework, NodeOutput.Rejected)
        workflow.add_edge(review, done, NodeOutput.Approved)

        # Save the workflow
        workflow.update_config(reposition=True)

        # Verify the workflow was created successfully
        updated_workflow = project.get_workflow()
        nodes = updated_workflow.get_nodes()
        edges = updated_workflow.get_edges()

        # Verify node count
        assert (
            len(nodes) == 5
        ), "Should have 5 nodes (2 initial + 1 review + 1 done + 1 rework)"

        # Verify edge count
        assert len(edges) == 4, "Should have 4 edges"

        # Verify node types exist
        node_types = [node.definition_id for node in nodes]
        assert (
            WorkflowDefinitionId.InitialLabelingTask in node_types
        ), "Should have InitialLabelingTask"
        assert (
            WorkflowDefinitionId.InitialReworkTask in node_types
        ), "Should have InitialReworkTask"
        assert (
            WorkflowDefinitionId.ReviewTask in node_types
        ), "Should have ReviewTask"
        assert WorkflowDefinitionId.Done in node_types, "Should have Done node"
        assert (
            WorkflowDefinitionId.SendToRework in node_types
        ), "Should have SendToRework node"

        # Verify review node has correct name
        review_nodes = [
            node
            for node in nodes
            if node.definition_id == WorkflowDefinitionId.ReviewTask
        ]
        assert len(review_nodes) == 1, "Should have exactly 1 review node"
        assert (
            review_nodes[0].name == "Test review task"
        ), "Review node should have correct name"

        # Verify initial labeling node has correct instructions
        initial_labeling_nodes = [
            node
            for node in nodes
            if node.definition_id == WorkflowDefinitionId.InitialLabelingTask
        ]
        assert (
            len(initial_labeling_nodes) == 1
        ), "Should have exactly 1 initial labeling node"
        assert (
            initial_labeling_nodes[0].instructions == "This is the entry point"
        ), "Initial labeling node should have correct instructions"

    finally:
        # Clean up the project
        project.delete()


def test_node_types(client, test_projects):
    """Test all node types to ensure they work correctly."""
    source_project, _ = test_projects

    workflow = source_project.get_workflow()

    initial_nodes = workflow.reset_to_initial_nodes(
        labeling_config=LabelingConfig(instructions="Start labeling")
    )

    review = workflow.add_node(type=NodeType.Review, name="Review Task")

    logic = workflow.add_node(type=NodeType.Logic, name="Logic Decision")

    rework = workflow.add_node(type=NodeType.Rework, name="Rework Task")

    custom_rework = workflow.add_node(
        type=NodeType.CustomRework,
        name="Custom Rework",
        instructions="Fix these issues",
    )

    done1 = workflow.add_node(type=NodeType.Done, name="Complete 1")
    done2 = workflow.add_node(type=NodeType.Done, name="Complete 2")

    workflow.add_edge(initial_nodes.labeling, review)
    workflow.add_edge(initial_nodes.rework, review)
    workflow.add_edge(review, logic, NodeOutput.Approved)
    workflow.add_edge(logic, rework, NodeOutput.If)
    workflow.add_edge(logic, custom_rework, NodeOutput.Else)
    workflow.add_edge(rework, done1)
    workflow.add_edge(custom_rework, done2)

    workflow.update_config(reposition=False)

    updated_workflow = source_project.get_workflow()
    nodes = updated_workflow.get_nodes()

    node_types = {}
    for node in nodes:
        node_type = node.definition_id
        if node_type not in node_types:
            node_types[node_type] = 0
        node_types[node_type] += 1

    assert node_types[WorkflowDefinitionId.InitialLabelingTask] == 1
    assert node_types[WorkflowDefinitionId.InitialReworkTask] == 1
    assert node_types[WorkflowDefinitionId.ReviewTask] == 1
    assert node_types[WorkflowDefinitionId.Logic] == 1
    assert node_types[WorkflowDefinitionId.SendToRework] == 1
    assert node_types[WorkflowDefinitionId.CustomReworkTask] == 1
    assert node_types[WorkflowDefinitionId.Done] == 2


def test_workflow_update_without_reset(client, test_projects):
    """Test updating an existing workflow by modifying node properties."""
    source_project, _ = test_projects

    # Create initial workflow
    workflow = source_project.get_workflow()

    initial_nodes = workflow.reset_to_initial_nodes(
        labeling_config=LabelingConfig(instructions="Original instructions")
    )
    review = workflow.add_node(type=NodeType.Review, name="Original Review")
    done = workflow.add_node(type=NodeType.Done, name="Original Done")

    workflow.add_edge(initial_nodes.labeling, review)
    workflow.add_edge(initial_nodes.rework, review)
    workflow.add_edge(review, done, NodeOutput.Approved)

    workflow.update_config(reposition=False)

    # Update workflow by modifying existing nodes
    updated_workflow = source_project.get_workflow()
    nodes = updated_workflow.get_nodes()

    # Update node properties
    for node in nodes:
        if node.definition_id == WorkflowDefinitionId.InitialLabelingTask:
            node.instructions = "Updated instructions"
        elif node.definition_id == WorkflowDefinitionId.ReviewTask:
            node.name = "Updated Review"
        elif node.definition_id == WorkflowDefinitionId.Done:
            node.name = "Updated Done"

    # Add new node and create separate done node to avoid multiple inputs
    new_logic = updated_workflow.add_node(
        type=NodeType.Logic,
        name="New Logic",
        filters=ProjectWorkflowFilter([sample(25)]),
    )

    # Create separate done node for the new logic path
    new_done = updated_workflow.add_node(type=NodeType.Done, name="Logic Done")

    # Update connections - create separate paths
    review_node = next(
        n for n in nodes if n.definition_id == WorkflowDefinitionId.ReviewTask
    )

    # Connect review rejected to logic, logic to new done
    updated_workflow.add_edge(review_node, new_logic, NodeOutput.Rejected)
    updated_workflow.add_edge(new_logic, new_done, NodeOutput.If)

    updated_workflow.update_config(reposition=False)

    # Verify updates were saved
    final_workflow = source_project.get_workflow()
    final_nodes = final_workflow.get_nodes()

    assert (
        len(final_nodes) == 6
    ), "Should have 6 nodes after adding logic and done nodes"

    # Verify property updates
    initial_labeling_nodes = [
        n
        for n in final_nodes
        if n.definition_id == WorkflowDefinitionId.InitialLabelingTask
    ]
    assert initial_labeling_nodes[0].instructions == "Updated instructions"

    review_nodes = [
        n
        for n in final_nodes
        if n.definition_id == WorkflowDefinitionId.ReviewTask
    ]
    assert review_nodes[0].name == "Updated Review"


def test_workflow_validation_in_update_config(client, test_projects):
    """Test the mandatory validation behavior in update_config."""
    source_project, _ = test_projects

    # Create an invalid workflow (missing connections)
    workflow = source_project.get_workflow()

    # Create workflow with required initial nodes but invalid connections
    initial_nodes = workflow.reset_to_initial_nodes()
    # Add a review node with no connections - this should cause validation errors
    review = workflow.add_node(type=NodeType.Review, name="Unconnected Review")

    # Only connect the initial nodes together, leaving review disconnected
    workflow.add_edge(
        initial_nodes.labeling, initial_nodes.rework
    )  # This is also invalid

    # Test 1: update_config should validate and fail with invalid workflow
    with pytest.raises(ValueError) as exc_info:
        workflow.update_config()

    assert "validation errors" in str(exc_info.value).lower()
    assert "Cannot update workflow configuration" in str(exc_info.value)

    # Test 2: Multiple calls should consistently fail validation
    with pytest.raises(ValueError) as exc_info:
        workflow.update_config()

    assert "validation errors" in str(exc_info.value).lower()

    # Test 3: Validation errors should be consistently reported
    with pytest.raises(ValueError) as exc_info:
        workflow.update_config()

    # Verify the error message is clear and helpful
    error_message = str(exc_info.value)
    assert "validation errors" in error_message.lower()
    assert "please fix these issues" in error_message.lower()

    # Test 4: Create a valid workflow and test successful update
    initial_nodes = workflow.reset_to_initial_nodes()
    review = workflow.add_node(type=NodeType.Review, name="Connected Review")
    done = workflow.add_node(type=NodeType.Done, name="Final")

    # Create proper connections
    workflow.add_edge(initial_nodes.labeling, review)
    workflow.add_edge(initial_nodes.rework, review)
    workflow.add_edge(review, done, NodeOutput.Approved)

    # This should work without errors
    result = workflow.update_config()
    assert result is not None

    # Test successful update - should not raise any exceptions
    try:
        workflow.update_config()
        # If we get here, the update was successful
        assert True
    except ValueError:
        # Should not happen with a valid workflow
        assert False, "Valid workflow should not raise validation errors"


def test_workflow_copy(client, test_projects):
    """Test copying a workflow between projects."""
    source_project, target_project = test_projects

    # Create source workflow
    source_workflow = source_project.get_workflow()

    initial_nodes = source_workflow.reset_to_initial_nodes(
        labeling_config=LabelingConfig(instructions="Source workflow")
    )
    review = source_workflow.add_node(
        type=NodeType.Review, name="Source Review"
    )
    logic = source_workflow.add_node(
        type=NodeType.Logic,
        name="Source Logic",
        filters=ProjectWorkflowFilter([labeled_by.is_one_of(["source-user"])]),
    )
    done = source_workflow.add_node(type=NodeType.Done, name="Source Done")

    source_workflow.add_edge(initial_nodes.labeling, review)
    source_workflow.add_edge(initial_nodes.rework, review)
    source_workflow.add_edge(review, logic, NodeOutput.Approved)
    source_workflow.add_edge(logic, done, NodeOutput.If)

    source_workflow.update_config(reposition=False)

    # Copy to target project
    target_project.clone_workflow_from(source_project.uid)

    # Verify copy
    target_workflow = target_project.get_workflow()
    source_nodes = source_workflow.get_nodes()
    target_nodes = target_workflow.get_nodes()

    assert len(source_nodes) == len(target_nodes), "Node count should match"

    source_node_types = sorted([n.definition_id.value for n in source_nodes])
    target_node_types = sorted([n.definition_id.value for n in target_nodes])
    assert source_node_types == target_node_types, "Node types should match"


def test_production_logic_node_with_comprehensive_filters(
    client, test_projects
):
    """Test creating and manipulating a production-like logic node with comprehensive filters."""
    source_project, _ = test_projects

    workflow = source_project.get_workflow()

    # Create basic workflow structure
    initial_nodes = workflow.reset_to_initial_nodes()
    done = workflow.add_node(type=NodeType.Done)

    # Create production-like logic node with comprehensive filters
    logic = workflow.add_node(
        type=NodeType.Logic,
        name="Production Logic",
        match_filters=MatchFilters.Any,
        filters=ProjectWorkflowFilter(
            [
                labeled_by.is_one_of(
                    ["cly7gzohg07zz07v5fqs63zmx", "cl7k7a9x1764808vk6bm1hf8e"]
                ),
                metadata([m_condition.contains("tag", ["test"])]),
                sample(23),
                labeled_at.between(
                    datetime(2024, 3, 9, 5, 5, 42),
                    datetime(2025, 4, 28, 13, 5, 42),
                ),
                labeling_time.greater_than(1000),
                review_time.less_than_or_equal(100),
                dataset.is_one_of(["cm37vyets000z072314wxgt0l"]),
                annotation.is_one_of(["cm37w0e0500lf0709ba7c42m9"]),
                consensus_average(0.17, 0.61),
                model_prediction(
                    [
                        mp_condition.is_one_of(
                            ["cm17qumj801ll07093toq47x3"], 1
                        ),
                        mp_condition.is_none(),
                    ]
                ),
                natural_language("Birds in the sky", 0.178, 0.768),
            ]
        ),
    )

    workflow.add_edge(initial_nodes.labeling, logic)
    workflow.add_edge(initial_nodes.rework, logic)
    workflow.add_edge(logic, done, NodeOutput.If)

    workflow.update_config(reposition=False)

    # Verify comprehensive filters
    updated_workflow = source_project.get_workflow()
    nodes = updated_workflow.get_nodes()
    logic_nodes = [
        n for n in nodes if n.definition_id == WorkflowDefinitionId.Logic
    ]
    assert len(logic_nodes) == 1, "Should have exactly one logic node"

    production_logic = logic_nodes[0]
    filters = production_logic.get_parsed_filters()

    assert (
        len(filters) >= 10
    ), f"Should have at least 10 filters, got {len(filters)}"

    # Verify filter logic is properly set
    assert production_logic.filter_logic in [
        "and",
        "or",
    ], "Should have valid filter logic"

    # Verify key filter types are present
    filter_fields = [f["field"] for f in filters]
    expected_fields = [
        "CreatedBy",
        "Metadata",
        "Sample",
        "LabeledAt",
        "LabelingTime",
        "Dataset",
        "ModelPrediction",
        "NlSearch",
    ]
    for field in expected_fields:
        assert field in filter_fields, f"Should have {field} filter"


def test_filter_operations_with_persistence(client, test_projects):
    """Test adding and removing filters with persistence."""
    source_project, _ = test_projects

    workflow = source_project.get_workflow()

    initial_nodes = workflow.reset_to_initial_nodes()
    done = workflow.add_node(type=NodeType.Done)

    # Create logic node with initial filters
    logic = workflow.add_node(
        type=NodeType.Logic,
        name="Filter Test",
        filters=ProjectWorkflowFilter(
            [
                labeled_by.is_one_of(["user1", "user2"]),
                sample(30),
                labeling_time.greater_than(500),
            ]
        ),
    )

    workflow.add_edge(initial_nodes.labeling, logic)
    workflow.add_edge(initial_nodes.rework, logic)
    workflow.add_edge(logic, done, NodeOutput.If)

    workflow.update_config(reposition=False)

    # Get logic node and verify initial filters
    updated_workflow = source_project.get_workflow()
    nodes = updated_workflow.get_nodes()
    logic_node = [
        n for n in nodes if n.definition_id == WorkflowDefinitionId.Logic
    ][0]

    initial_filters = logic_node.get_parsed_filters()
    initial_count = len(initial_filters)
    assert (
        initial_count == 3
    ), f"Should start with 3 filters, got {initial_count}"

    # Test removing filters with persistence
    logic_node.remove_filter(FilterField.LabeledBy)
    logic_node.remove_filter(FilterField.Sample)
    updated_workflow.update_config(reposition=False)

    # Verify removals persisted
    workflow_after_removal = source_project.get_workflow()
    nodes_after_removal = workflow_after_removal.get_nodes()
    logic_after_removal = [
        n
        for n in nodes_after_removal
        if n.definition_id == WorkflowDefinitionId.Logic
    ][0]

    filters_after_removal = logic_after_removal.get_parsed_filters()
    assert (
        len(filters_after_removal) == 1
    ), "Should have 1 filter after removing 2"

    remaining_fields = [f["field"] for f in filters_after_removal]
    assert (
        "LabelingTime" in remaining_fields
    ), "LabelingTime filter should remain"
    assert (
        "CreatedBy" not in remaining_fields
    ), "LabeledBy filter should be removed"

    # Test adding filters with persistence
    logic_after_removal.add_filter(dataset.is_one_of(["new-dataset"]))
    logic_after_removal.add_filter(
        metadata([m_condition.starts_with("priority", "high")])
    )
    workflow_after_removal.update_config(reposition=False)

    # Verify additions persisted
    final_workflow = source_project.get_workflow()
    final_nodes = final_workflow.get_nodes()
    final_logic = [
        n for n in final_nodes if n.definition_id == WorkflowDefinitionId.Logic
    ][0]

    final_filters = final_logic.get_parsed_filters()
    assert len(final_filters) == 3, "Should have 3 filters after adding 2"

    final_fields = [f["field"] for f in final_filters]
    assert "Dataset" in final_fields, "Dataset filter should be added"
    assert "Metadata" in final_fields, "Metadata filter should be added"


def test_node_removal_with_validation(client, test_projects):
    """Test removing nodes while maintaining workflow validity."""
    source_project, _ = test_projects

    workflow = source_project.get_workflow()

    # Create workflow with removable nodes
    initial_nodes = workflow.reset_to_initial_nodes()
    review = workflow.add_node(type=NodeType.Review, name="Primary Review")
    logic = workflow.add_node(
        type=NodeType.Logic,
        name="Quality Gate",
        filters=ProjectWorkflowFilter([sample(15)]),
    )

    # Multiple terminal nodes for safe removal
    done_high = workflow.add_node(type=NodeType.Done, name="High Quality")
    done_standard = workflow.add_node(type=NodeType.Done, name="Standard")
    secondary_review = workflow.add_node(
        type=NodeType.Review, name="Secondary Review"
    )
    done_final = workflow.add_node(type=NodeType.Done, name="Final")

    # Create connections
    workflow.add_edge(initial_nodes.labeling, review)
    workflow.add_edge(initial_nodes.rework, review)
    workflow.add_edge(review, logic, NodeOutput.Approved)
    workflow.add_edge(logic, done_high, NodeOutput.If)
    workflow.add_edge(logic, secondary_review, NodeOutput.Else)
    workflow.add_edge(secondary_review, done_standard, NodeOutput.Approved)
    workflow.add_edge(secondary_review, done_final, NodeOutput.Rejected)

    workflow.update_config(reposition=False)

    initial_workflow = source_project.get_workflow()
    initial_nodes = initial_workflow.get_nodes()
    assert len(initial_nodes) == 8, "Should start with 8 nodes"

    # Remove terminal nodes safely and reroute connections
    nodes_to_remove = [
        n for n in initial_nodes if n.name in ["Standard", "Final"]
    ]

    # Before removing, create proper rework node and reroute connections
    secondary_review_node = next(
        n for n in initial_nodes if n.name == "Secondary Review"
    )

    # Create separate nodes for rerouting (can't reuse done_high as it already has input from logic)
    done_approved = initial_workflow.add_node(
        type=NodeType.Done, name="Review Approved"
    )
    rework_node = initial_workflow.add_node(
        type=NodeType.Rework, name="Secondary Rework"
    )

    # Proper workflow logic: Approved -> New Done, Rejected -> Rework
    initial_workflow.add_edge(
        secondary_review_node, done_approved, NodeOutput.Approved
    )
    initial_workflow.add_edge(
        secondary_review_node, rework_node, NodeOutput.Rejected
    )

    # Now remove the terminal nodes
    initial_workflow.delete_nodes(nodes_to_remove)
    initial_workflow.update_config(reposition=False)

    # Verify nodes were removed and connections rerouted
    final_workflow = source_project.get_workflow()
    final_nodes = final_workflow.get_nodes()
    assert (
        len(final_nodes) == 8
    ), "Should have 8 nodes after removal and new node addition"

    # Verify removed nodes are gone
    final_node_names = [n.name for n in final_nodes]
    assert "Standard" not in final_node_names, "Standard node should be removed"
    assert "Final" not in final_node_names, "Final node should be removed"

    # Verify key nodes still exist
    assert "High Quality" in final_node_names, "High Quality node should exist"
    assert (
        "Secondary Review" in final_node_names
    ), "Secondary Review node should exist"
    assert (
        "Review Approved" in final_node_names
    ), "Review Approved node should exist"
    assert (
        "Secondary Rework" in final_node_names
    ), "Secondary Rework node should exist"


def test_metadata_multiple_conditions():
    """Test metadata filter with multiple conditions."""
    multi_filter = {
        "metadata": [
            {"key": "source", "operator": "ends_with", "value": "test1"},
            {"key": "tag", "operator": "starts_with", "value": "test2"},
        ]
    }

    api_result = convert_to_api_format(multi_filter)

    assert api_result["field"] == "Metadata"
    assert api_result["operator"] == "is"
    assert api_result["value"] == "2 metadata conditions selected"
    assert len(api_result["metadata"]["filters"]) == 2


def test_model_prediction_conditions(client, test_projects):
    """Test model prediction filters with various conditions."""
    source_project, _ = test_projects

    workflow = source_project.get_workflow()

    initial_nodes = workflow.reset_to_initial_nodes()
    done = workflow.add_node(type=NodeType.Done)

    # Test different model prediction conditions
    logic_none = workflow.add_node(
        type=NodeType.Logic,
        name="Model None",
        filters=ProjectWorkflowFilter(
            [model_prediction([mp_condition.is_none()])]
        ),
    )

    logic_one_of = workflow.add_node(
        type=NodeType.Logic,
        name="Model One Of",
        filters=ProjectWorkflowFilter(
            [
                model_prediction(
                    [mp_condition.is_one_of(["model1", "model2"], 0.7, 0.95)]
                )
            ]
        ),
    )

    # Create connections
    workflow.add_edge(initial_nodes.labeling, logic_none)
    workflow.add_edge(initial_nodes.rework, logic_none)
    workflow.add_edge(logic_none, logic_one_of, NodeOutput.If)
    workflow.add_edge(logic_one_of, done, NodeOutput.If)

    workflow.update_config(reposition=False)

    # Verify model prediction filters
    updated_workflow = source_project.get_workflow()
    nodes = updated_workflow.get_nodes()
    logic_nodes = [
        n for n in nodes if n.definition_id == WorkflowDefinitionId.Logic
    ]

    assert len(logic_nodes) == 2, "Should have 2 model prediction test nodes"

    for node in logic_nodes:
        filters = node.get_parsed_filters()
        assert len(filters) == 1, "Each node should have exactly 1 filter"
        assert (
            filters[0]["field"] == "ModelPrediction"
        ), "Should have ModelPrediction filter"


def test_reset_to_initial_nodes_preserves_existing_ids(client):
    """Test that reset_to_initial_nodes preserves existing initial node IDs."""
    # Create a new project for this test
    project_name = f"ID Preservation Test {uuid.uuid4()}"
    project = client.create_project(
        name=project_name, media_type=MediaType.Image
    )

    try:
        # Get workflow and create initial nodes
        workflow = project.get_workflow()
        initial_nodes = workflow.reset_to_initial_nodes()

        # Create a complete workflow by adding nodes and edges
        done_node = workflow.add_node(type=NodeType.Done, name="Test Done")
        workflow.add_edge(initial_nodes.labeling, done_node)
        workflow.add_edge(initial_nodes.rework, done_node)

        # Record the original IDs
        original_labeling_id = initial_nodes.labeling.id
        original_rework_id = initial_nodes.rework.id

        # Update the workflow to save the initial state (now valid)
        workflow.update_config()

        # Reset again with new configuration
        new_initial_nodes = workflow.reset_to_initial_nodes(
            labeling_config=LabelingConfig(
                instructions="Updated instructions",
                max_contributions_per_user=5,
            ),
            rework_config=ReworkConfig(
                instructions="Updated rework instructions",
                max_contributions_per_user=3,
            ),
        )

        # Rebuild the workflow structure after reset
        done_node = workflow.add_node(type=NodeType.Done, name="Test Done")
        workflow.add_edge(new_initial_nodes.labeling, done_node)
        workflow.add_edge(new_initial_nodes.rework, done_node)

        # Verify that the IDs are preserved
        assert new_initial_nodes.labeling.id == original_labeling_id, (
            f"InitialLabelingNode ID changed from {original_labeling_id} to {new_initial_nodes.labeling.id}. "
            f"This will break the workflow!"
        )
        assert new_initial_nodes.rework.id == original_rework_id, (
            f"InitialReworkNode ID changed from {original_rework_id} to {new_initial_nodes.rework.id}. "
            f"This will break the workflow!"
        )

        # Verify that the configuration was updated
        assert new_initial_nodes.labeling.instructions == "Updated instructions"
        assert new_initial_nodes.labeling.max_contributions_per_user == 5
        assert (
            new_initial_nodes.rework.instructions
            == "Updated rework instructions"
        )
        assert new_initial_nodes.rework.max_contributions_per_user == 3

        # Save and verify the workflow still works
        workflow.update_config()

        # Reload the workflow and verify IDs are still preserved
        reloaded_workflow = project.get_workflow()
        reloaded_nodes = reloaded_workflow.get_nodes()

        labeling_node = next(
            n
            for n in reloaded_nodes
            if n.definition_id == WorkflowDefinitionId.InitialLabelingTask
        )
        rework_node = next(
            n
            for n in reloaded_nodes
            if n.definition_id == WorkflowDefinitionId.InitialReworkTask
        )

        assert labeling_node.id == original_labeling_id
        assert rework_node.id == original_rework_id

    finally:
        project.delete()


def test_copy_workflow_preserves_initial_node_ids(client):
    """Test that copy operations preserve existing initial node IDs."""
    # Create source and target projects
    source_project = client.create_project(
        name=f"Source Project {uuid.uuid4()}", media_type=MediaType.Image
    )
    target_project = client.create_project(
        name=f"Target Project {uuid.uuid4()}", media_type=MediaType.Image
    )

    try:
        # Set up source workflow
        source_workflow = source_project.get_workflow()
        source_initial = source_workflow.reset_to_initial_nodes()
        done_node = source_workflow.add_node(type=NodeType.Done)
        source_workflow.add_edge(source_initial.labeling, done_node)
        source_workflow.add_edge(source_initial.rework, done_node)
        source_workflow.update_config()

        # Set up target workflow with its own initial nodes
        target_workflow = target_project.get_workflow()
        target_initial = target_workflow.reset_to_initial_nodes()

        # Record original target initial node IDs
        original_target_labeling_id = target_initial.labeling.id
        original_target_rework_id = target_initial.rework.id

        # Copy from source to target
        target_workflow.copy_from(source_workflow)

        # Verify that target's initial node IDs are preserved
        updated_nodes = target_workflow.get_nodes()

        labeling_node = next(
            n
            for n in updated_nodes
            if n.definition_id == WorkflowDefinitionId.InitialLabelingTask
        )
        rework_node = next(
            n
            for n in updated_nodes
            if n.definition_id == WorkflowDefinitionId.InitialReworkTask
        )

        assert labeling_node.id == original_target_labeling_id, (
            f"Target InitialLabelingNode ID changed from {original_target_labeling_id} to {labeling_node.id}. "
            f"This will break the workflow!"
        )
        assert rework_node.id == original_target_rework_id, (
            f"Target InitialReworkNode ID changed from {original_target_rework_id} to {rework_node.id}. "
            f"This will break the workflow!"
        )

        # Verify the structure was copied (should have a Done node)
        done_nodes = [
            n
            for n in updated_nodes
            if n.definition_id == WorkflowDefinitionId.Done
        ]
        assert len(done_nodes) == 1, "Done node should have been copied"

    finally:
        source_project.delete()
        target_project.delete()


def test_edge_id_format_is_correct(client):
    """Test that edge IDs are generated using the correct format."""
    # Create a new project for this test
    project_name = f"Edge ID Format Test {uuid.uuid4()}"
    project = client.create_project(
        name=project_name, media_type=MediaType.Image
    )

    try:
        # Get workflow and create initial nodes
        workflow = project.get_workflow()
        initial_nodes = workflow.reset_to_initial_nodes()

        # Create a done node
        done_node = workflow.add_node(type=NodeType.Done, name="Test Done")

        # Create edges with different handle types
        edge1 = workflow.add_edge(
            initial_nodes.labeling, done_node, NodeOutput.If
        )
        edge2 = workflow.add_edge(
            initial_nodes.rework, done_node, NodeOutput.If
        )

        # Verify edge ID format: xy-edge__{source}{sourceHandle}-{target}{targetHandle}
        expected_edge1_id = (
            f"xy-edge__{initial_nodes.labeling.id}if-{done_node.id}in"
        )
        expected_edge2_id = (
            f"xy-edge__{initial_nodes.rework.id}if-{done_node.id}in"
        )

        assert (
            edge1.id == expected_edge1_id
        ), f"Edge ID format incorrect. Expected: {expected_edge1_id}, Got: {edge1.id}"
        assert (
            edge2.id == expected_edge2_id
        ), f"Edge ID format incorrect. Expected: {expected_edge2_id}, Got: {edge2.id}"

        # Verify edge properties are correct
        assert edge1.source == initial_nodes.labeling.id
        assert edge1.target == done_node.id
        assert edge1.sourceHandle == "if"
        assert edge1.targetHandle == "in"

        assert edge2.source == initial_nodes.rework.id
        assert edge2.target == done_node.id
        assert edge2.sourceHandle == "if"
        assert edge2.targetHandle == "in"

        # Save and verify the workflow
        workflow.update_config()

        # Reload workflow and check edge IDs are preserved
        reloaded_workflow = project.get_workflow()
        reloaded_edges = reloaded_workflow.get_edges()

        edge_ids = [edge.id for edge in reloaded_edges]
        assert (
            expected_edge1_id in edge_ids
        ), f"Edge ID {expected_edge1_id} not found after reload"
        assert (
            expected_edge2_id in edge_ids
        ), f"Edge ID {expected_edge2_id} not found after reload"

    finally:
        project.delete()


def test_edge_id_format_with_different_handles(client):
    """Test edge ID format with different source handle types."""
    # Create a new project for this test
    project_name = f"Edge Handle Test {uuid.uuid4()}"
    project = client.create_project(
        name=project_name, media_type=MediaType.Image
    )

    try:
        # Create workflow with review node
        workflow = project.get_workflow()
        initial_nodes = workflow.reset_to_initial_nodes()

        review_node = workflow.add_node(
            type=NodeType.Review, name="Test Review"
        )
        done_node = workflow.add_node(type=NodeType.Done, name="Approved")
        rework_node = workflow.add_node(type=NodeType.Rework, name="Rejected")

        # Connect initial to review
        workflow.add_edge(initial_nodes.labeling, review_node)

        # Create edges with different handle types
        approved_edge = workflow.add_edge(
            review_node, done_node, NodeOutput.Approved
        )
        rejected_edge = workflow.add_edge(
            review_node, rework_node, NodeOutput.Rejected
        )

        # Verify edge ID formats - NodeOutput.Approved maps to "if", NodeOutput.Rejected maps to "else"
        expected_approved_id = f"xy-edge__{review_node.id}if-{done_node.id}in"
        expected_rejected_id = (
            f"xy-edge__{review_node.id}else-{rework_node.id}in"
        )

        assert (
            approved_edge.id == expected_approved_id
        ), f"Approved edge ID format incorrect. Expected: {expected_approved_id}, Got: {approved_edge.id}"
        assert (
            rejected_edge.id == expected_rejected_id
        ), f"Rejected edge ID format incorrect. Expected: {expected_rejected_id}, Got: {rejected_edge.id}"

        # Verify handle values - NodeOutput.Approved maps to "if", NodeOutput.Rejected maps to "else"
        assert approved_edge.sourceHandle == "if"
        assert rejected_edge.sourceHandle == "else"
        assert approved_edge.targetHandle == "in"
        assert rejected_edge.targetHandle == "in"

    finally:
        project.delete()
