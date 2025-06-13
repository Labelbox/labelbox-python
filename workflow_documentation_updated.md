---
title: "Workflow"
slug: "workflow"
excerpt: "Developer guide for creating and modifying workflows via the Python SDK."
category: 
order: 1
hidden: false
---

# Client

```python
import labelbox as lb
client = lb.Client(api_key="<YOUR_API_KEY>")
```

***

# Fundamentals

> 📘 Preview feature
> 
> Workflow management is a [preview](doc:product-release-phases#preview) feature.

Workflows are connected to the `Project` class and are generated automatically during project creation. Like `Batch`, workflows help organize and control the flow of labeling tasks through different stages.

Key concepts:
- Workflows are composed of **nodes** and **edges**
- Each node can have only one input connection, except when both `Initial labeling task` and `Rework (All Rejected)` nodes serve as inputs to a single downstream node
- No changes are pushed to the platform until you call `update_config()`
- All nodes must be connected for the workflow to be valid

## Access a workflow
```python
workflow = project.get_workflow()
```

## Clone a workflow from a different project
```python
project_source_id = "<project_source_id>"
project_target_id = "<project_target_id>"
project_source = client.get_project(project_source_id)
project_target = client.get_project(project_target_id)

project_target.clone_workflow_from(project_source.uid)
```

## Reset a workflow
This creates a blank workflow canvas with initial nodes. Use this step if you want to start from scratch.

```python
initial_nodes = workflow.reset_to_initial_nodes()
```

## Commit changes
To push changes made to a workflow, you must use `update_config()`.

```python
# Commit changes without changing node locations
workflow.update_config()

# Commit changes and attempt to realign nodes
workflow.update_config(reposition=True)
```

## Validate a workflow
Before committing changes, you can check if your workflow configuration is valid:

```python
validation_result = workflow.check_validity()
if validation_result.get("errors"):
    print("Workflow has errors:", validation_result["errors"])
else:
    print("Workflow is valid")
    workflow.update_config()
```

## Add a node
Types of nodes are accessible through the enum `NodeType`:

**Initial nodes:**
- `NodeType.InitialLabeling` - Entry point for new labeling tasks
- `NodeType.InitialRework` - Entry point for tasks that need to be reworked

**Step nodes:**
- `NodeType.Review` - Review completed labels
- `NodeType.Logic` - Apply filters to route tasks conditionally
- `NodeType.CustomRework` - Custom rework step with configurable settings

**Terminal nodes:**
- `NodeType.Done` - Marks tasks as completed
- `NodeType.Rework` - Sends tasks back to the rework queue

> 📘 Note
> 
> `NodeType.CustomRework` can be used as a terminal node or be connected to another node.

```python 
from labelbox.schema.workflow import NodeType

new_node = workflow.add_node(type=NodeType.InitialLabeling)
```

## Delete a node
This automatically removes connected edges.

```python
# Get nodes to delete
nodes_to_delete = [
    node
    for node in workflow.get_nodes()
    if node.name == "NodeToDelete"
]

workflow.delete_nodes(nodes_to_delete)
```

## Add an edge
Edges connect the output of a source node to the input of a target node. All nodes must be connected in the workflow. The output of the CustomRework node is optional.

Types of outputs are listed in the enum `NodeOutput`:
- `NodeOutput.If` (default value, can be omitted)
- `NodeOutput.Else`
- `NodeOutput.Approved`
- `NodeOutput.Rejected`

### Outputs per node
| Node | Available Outputs |
| :--- | :-- |
| InitialLabeling | `NodeOutput.If` |
| InitialRework | `NodeOutput.If` |
| Review | `NodeOutput.Approved`, `NodeOutput.Rejected` |
| Logic | `NodeOutput.If`, `NodeOutput.Else` |
| CustomRework | Optional `NodeOutput.If` |
| Done | None (terminal node) |
| Rework | None (terminal node) |

```python
from labelbox.schema.workflow import NodeOutput

# Connect nodes with appropriate outputs
workflow.add_edge(initial_labeling, initial_review) # Default NodeOutput.If
workflow.add_edge(initial_rework, initial_review)
workflow.add_edge(initial_review, logic, NodeOutput.Approved)
workflow.add_edge(initial_review, rework_node, NodeOutput.Rejected)
workflow.add_edge(logic, done, NodeOutput.If) # NodeOutput.If can be omitted
workflow.add_edge(logic, custom_rework_1, NodeOutput.Else)
```

## Node attributes
The following attributes can be configured for each node type:

| Node | Configurable Attributes |
| :--- | :-- |
| InitialLabeling | `instructions`, `max_contributions_per_user` |
| InitialRework | `instructions`, `individual_assignment`, `max_contributions_per_user` |
| Review | `instructions`, `group_assignment`, `max_contributions_per_user` |
| Logic | `name`, `match_filters`, `filters` |
| CustomRework | `name`, `instructions`, `group_assignment`, `individual_assignment`, `max_contributions_per_user` |
| Done | `name` |
| Rework | `name` |

**Common attributes:**
- `max_contributions_per_user`: Maximum number of labels per task queue (empty for no limit)
- `instructions`: Custom instructions for labelers working on this node
- `group_assignment`: List of user group IDs assigned to this node
- `individual_assignment`: Individual assignment strategy (see `IndividualAssignment` enum)

## Logic node
The Logic node contains filters that determine how tasks flow through the workflow. The `match_filters` attribute controls how multiple filters are evaluated:
- `MatchFilters.Any`: Match any of the filters (OR logic)
- `MatchFilters.All`: Match all of the filters (AND logic)

### Available filters
Each filter type can be used at most once per Logic node.

#### created_by
Filter by the user who created the label.

**Operators:** None (direct list filter)

```python
from labelbox.schema.workflow import created_by

# Using named parameter
created_by(user_ids=["<user_1_id>", "<user_2_id>"])

# Using positional parameter
created_by(["<user_1_id>", "<user_2_id>"])
```

#### metadata
Filter by data row metadata values.

**Operators:** 
- `contains`
- `starts_with`
- `ends_with`
- `does_not_contain`
- `is_any`
- `is_not_any`

```python
from labelbox.schema.workflow import metadata, m_condition

# Using named parameters
metadata(conditions=[m_condition.contains(key="<metadata_schema_id>", value=["test"])])

# Using positional parameters
metadata([m_condition.contains("<metadata_schema_id>", ["test"])])
```

#### sample
Filter by percentage sampling.

**Operators:** None (percentage value)

```python
from labelbox.schema.workflow import sample

# Using named parameter
sample(percentage=23)

# Using positional parameter
sample(23)
```

#### labeled_at
Filter by when the label was created.

**Operators:** 
- `between`

```python
from labelbox.schema.workflow import labeled_at
from datetime import datetime

# Using named parameters
labeled_at.between(
    start=datetime(2024, 3, 9, 5, 5, 42), 
    end=datetime(2025, 4, 28, 13, 5, 42)
)

# Using positional parameters
labeled_at.between(
    datetime(2024, 3, 9, 5, 5, 42), 
    datetime(2025, 4, 28, 13, 5, 42)
)
```

#### labeling_time
Filter by how long it took to create the label.

**Operators:** 
- `greater_than`
- `less_than`
- `greater_than_or_equal`
- `less_than_or_equal`
- `between`

```python
from labelbox.schema.workflow import labeling_time

# Using named parameter
labeling_time.greater_than(seconds=1000)

# Using positional parameter
labeling_time.greater_than(1000)
```

#### review_time
Filter by how long it took to review the label.

**Operators:** 
- `greater_than`
- `less_than`
- `greater_than_or_equal`
- `less_than_or_equal`
- `between`

```python
from labelbox.schema.workflow import review_time

# Using named parameter
review_time.less_than_or_equal(seconds=100)

# Using positional parameter
review_time.less_than_or_equal(100)
```

#### issue_category
Filter by issue categories flagged during review.

**Operators:** None (direct list filter)

```python
from labelbox.schema.workflow import issue_category

# Using named parameter
issue_category(category_ids=["<issue_category_id>"])

# Using positional parameter
issue_category(["<issue_category_id>"])
```

#### batch
Filter by batch membership.

**Operators:** 
- `is_one_of`
- `is_not_one_of`

```python
from labelbox.schema.workflow import batch

# Using named parameter
batch.is_one_of(values=["<batch_id>"])

# Using positional parameter
batch.is_one_of(["<batch_id>"])
```

#### dataset
Filter by dataset membership.

**Operators:** None (direct list filter)

```python
from labelbox.schema.workflow import dataset

# Using named parameter
dataset(dataset_ids=["<dataset_id>"])

# Using positional parameter
dataset(["<dataset_id>"])
```

#### annotation
Filter by the presence of specific annotations. `schema_node_ids` is a list of schema node IDs that correspond to tools or classifications defined in the project's ontology schema.

**Operators:** None (direct list filter)

```python
from labelbox.schema.workflow import annotation

# Using named parameter
annotation(schema_node_ids=["<schema_node_id>"])

# Using positional parameter
annotation(["<schema_node_id>"])
```

#### consensus_average
Filter by overall consensus score.

**Operators:** None (range filter with min/max)

```python
from labelbox.schema.workflow import consensus_average

# Using named parameters
consensus_average(min=0.17, max=0.61)

# Using positional parameters
consensus_average(0.17, 0.61)
```

#### feature_consensus_average
Filter by consensus score for specific features. `annotations` is a list of schema node IDs that correspond to tools or classifications defined in the project's ontology schema.

**Operators:** None (range filter with min/max and annotation list)

```python
from labelbox.schema.workflow import feature_consensus_average

# Using named parameters
feature_consensus_average(min=0.17, max=0.67, annotations=["<schema_node_id>"])

# Using positional parameters
feature_consensus_average(0.17, 0.67, ["<schema_node_id>"])
```

#### model_prediction
Filter by model predictions. Model predictions use a list of conditions named `mp_condition`. The `is_none` operator takes precedence over other operators.

**Operators:** 
- `is_one_of`
- `is_not_one_of`
- `is_none`

```python
from labelbox.schema.workflow import model_prediction, mp_condition

# Using named parameter
model_prediction(conditions=[
    mp_condition.is_one_of(models=["<model_id>"], min_score=1),
    mp_condition.is_not_one_of(models=["<model_id>"], min_score=2, max_score=6),
    mp_condition.is_none()
])

# Using positional parameter
model_prediction([
    mp_condition.is_one_of(["<model_id>"], 1),
    mp_condition.is_not_one_of(["<model_id>"], 2, 6),
    mp_condition.is_none()
])
```

#### natural_language
Filter using semantic search. The `content` (or prompt) follows this format:
`"Find this / more of this / not this / bias_value"`
where `bias_value` is a number between 0 and 1.

**Operators:** None (semantic search with score range)

```python
from labelbox.schema.workflow import natural_language

# Using named parameters
natural_language(
    content="Birds in the sky/Blue sky/clouds/0.5", 
    min_score=0.178, 
    max_score=0.768
)

# Using positional parameters
natural_language("Birds in the sky/Blue sky/clouds/0.5", 0.178, 0.768)
```

### Managing filters on Logic nodes

```python
from labelbox.schema.workflow.enums import WorkflowDefinitionId, FilterField
from labelbox.schema.workflow import mp_condition, model_prediction

workflow = project.get_workflow()

# Get the Logic node
logic = next(
    node for node in workflow.get_nodes()
    if node.definition_id == WorkflowDefinitionId.Logic
)
# Alternative: get by node ID
# logic = workflow.get_node_by_id("0359113a-6081-4f48-83d1-175062a0259b")

# Remove a filter based on its type 
logic.remove_filter(FilterField.ModelPrediction)

# Add a filter
logic.add_filter(
    model_prediction([
        mp_condition.is_none()
    ])
)

# Apply changes
workflow.update_config()
```

## Example: Create a minimal workflow
The following creates a basic workflow with three nodes:
- Initial labeling task
- Rework (all rejected)
- Done

```python
import labelbox as lb
from labelbox.schema.workflow import NodeType

# Initialize client and project
client = lb.Client(api_key="<YOUR_API_KEY>")
project_id = "<project_id>"
project = client.get_project(project_id)

# Get workflow and reset to start fresh
workflow = project.get_workflow()
initial_nodes = workflow.reset_to_initial_nodes()

# Create nodes
initial_labeling = workflow.add_node(type=NodeType.InitialLabeling)
initial_rework = workflow.add_node(type=NodeType.InitialRework)
done = workflow.add_node(type=NodeType.Done)

# Connect nodes
workflow.add_edge(initial_labeling, done)
workflow.add_edge(initial_rework, done)

# Validate and commit changes
validation_result = workflow.check_validity()
if not validation_result.get("errors"):
    workflow.update_config(reposition=True)
    print("Workflow created successfully!")
else:
    print("Workflow validation errors:", validation_result["errors"])
```

## Example: Complete workflow showcase
The following example demonstrates all node types and filter options:

```python
import labelbox as lb
from labelbox.schema.workflow import (
    NodeType, 
    NodeOutput, 
    ProjectWorkflowFilter,
    created_by,
    metadata,
    sample,
    labeled_at,
    mp_condition,
    m_condition,
    labeling_time,
    review_time,
    issue_category,
    batch,
    dataset,
    annotation,
    consensus_average,
    model_prediction,
    natural_language,
    feature_consensus_average
)
from labelbox.schema.workflow.enums import IndividualAssignment, MatchFilters
from datetime import datetime

# Initialize client and project
client = lb.Client(api_key="<YOUR_API_KEY>")
project_id = "<project_id>"
project = client.get_project(project_id)

# Get workflow and reset config
workflow = project.get_workflow()
initial_nodes = workflow.reset_to_initial_nodes()

# Create nodes with configurations
initial_labeling = workflow.add_node(
    type=NodeType.InitialLabeling,
    instructions="This is the entry point for new labeling tasks",
    max_contributions_per_user=10
)

initial_rework = workflow.add_node(
    type=NodeType.InitialRework,
    individual_assignment=IndividualAssignment.LabelCreator
)

initial_review = workflow.add_node(
    type=NodeType.Review,
    name="Initial review task",
    group_assignment=["<user_group_id_1>", "<user_group_id_2>"]
)

logic = workflow.add_node(
    type=NodeType.Logic,
    name="Logic node",
    match_filters=MatchFilters.Any,
    filters=ProjectWorkflowFilter([
        created_by(["<user_id_1>", "<user_id_2>", "<user_id_3>"]),
        metadata([m_condition.contains("<metadata_schema_id>", ["test"])]),
        sample(23),
        labeled_at.between(
            datetime(2024, 3, 9, 5, 5, 42), 
            datetime(2025, 4, 28, 13, 5, 42)
        ),
        labeling_time.greater_than(1000),
        review_time.less_than_or_equal(100),
        issue_category(["<issue_category_id>"]),
        batch.is_one_of(["<batch_id>"]),
        dataset(["<dataset_id>"]),
        annotation(["<schema_node_id>"]),
        consensus_average(0.17, 0.61),
        model_prediction([
            mp_condition.is_one_of(["<model_id_1>"], 1),
            mp_condition.is_not_one_of(["<model_id_2>"], 2, 6),
            mp_condition.is_none()
        ]),
        natural_language("Birds in the sky/Blue sky/clouds/0.5", 0.178, 0.768),
        feature_consensus_average(0.17, 0.67, ["<schema_node_id>"])
    ])
)

# Terminal and step nodes
done = workflow.add_node(type=NodeType.Done)
rework = workflow.add_node(type=NodeType.Rework, name="To rework")

custom_rework_1 = workflow.add_node(
    type=NodeType.CustomRework,
    name="Custom Rework 1",
    individual_assignment=IndividualAssignment.LabelCreator,
    group_assignment=["<user_group_id_1>", "<user_group_id_2>"]
)

review_2 = workflow.add_node(
    type=NodeType.Review,
    name="Review 2"
)

custom_rework_2 = workflow.add_node(
    type=NodeType.CustomRework,
    name="Custom Rework 2",
    instructions="Additional rework instructions"
)

done_2 = workflow.add_node(
    type=NodeType.Done,
    name="Ready for final review"
)

# Create edges between nodes
workflow.add_edge(initial_labeling, initial_review)
workflow.add_edge(initial_rework, initial_review)
workflow.add_edge(initial_review, logic, NodeOutput.Approved)
workflow.add_edge(initial_review, rework, NodeOutput.Rejected)
workflow.add_edge(logic, review_2, NodeOutput.If)
workflow.add_edge(logic, custom_rework_1, NodeOutput.Else)
workflow.add_edge(review_2, done, NodeOutput.Approved)
workflow.add_edge(review_2, custom_rework_2, NodeOutput.Rejected)
workflow.add_edge(custom_rework_2, done_2)

# Validate and commit the workflow
validation_result = workflow.check_validity()
if not validation_result.get("errors"):
    workflow.update_config(reposition=True)
    print("Complex workflow created successfully!")
else:
    print("Workflow validation errors:", validation_result["errors"])
``` 