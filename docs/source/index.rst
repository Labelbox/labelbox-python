Labelbox Python API reference
===================================

.. toctree::
   :maxdepth: 3
   :caption: Contents:

Client
----------------------

.. automodule:: labelbox.client
   :members:
   :special-members: __init__
   :exclude-members: upload_data, upload_file
   :show-inheritance:

AssetAttachment
--------------------------------------

.. automodule:: labelbox.schema.asset_attachment
   :members:
   :show-inheritance:


Benchmark
--------------------------------

.. automodule:: labelbox.schema.benchmark
   :members:
   :show-inheritance:

BulkImportRequest
--------------------------------------------

.. automodule:: labelbox.schema.bulk_import_request
   :members:
   :exclude-members: create_from_local_file, create_from_objects, create_from_url, from_name
   :show-inheritance:

DataRow
--------------------------------

.. automodule:: labelbox.schema.data_row
   :members:
   :show-inheritance:

Dataset
------------------------------

.. automodule:: labelbox.schema.dataset
   :members:
   :show-inheritance:

Label
----------------------------

.. automodule:: labelbox.schema.label
   :members:
   :show-inheritance:

LabelingFrontend
-----------------------------------------

.. automodule:: labelbox.schema.labeling_frontend
   :members: LabelingFrontend
   :exclude-members: LabelingFrontendOptions
   :show-inheritance:

LabelingFrontendOptions
-----------------------------------------
.. automodule:: labelbox.schema.labeling_frontend
   :members: LabelingFrontendOptions
   :exclude-members: LabelingFrontend
   :show-inheritance:
   :noindex:

LabelingParameterOverride
-----------------------------------------
.. automodule:: labelbox.schema.project
    :members: LabelingParameterOverride
    :show-inheritance:
    :noindex:

Ontology
-------------------------------

.. automodule:: labelbox.schema.ontology
   :members:
   :exclude-members: OntologyEntity, Classification, Tool, Option
   :show-inheritance:

Organization
-----------------------------------

.. automodule:: labelbox.schema.organization
   :members:
   :show-inheritance:

Project
------------------------------

.. automodule:: labelbox.schema.project
   :members:
   :exclude-members: LabelerPerformance, LabelingParameterOverride
   :show-inheritance:

Review
-----------------------------

.. automodule:: labelbox.schema.review
   :members:
   :show-inheritance:

Task
---------------------------

.. automodule:: labelbox.schema.task
   :members:
   :show-inheritance:

Task Queue
---------------------------
.. automodule:: labelbox.schema.task_queue
   :members:
   :show-inheritance:

User
---------------------------

.. automodule:: labelbox.schema.user
   :members:
   :show-inheritance:

Webhook
------------------------------

.. automodule:: labelbox.schema.webhook
   :members:
   :show-inheritance:

Exceptions
--------------------------

.. automodule:: labelbox.exceptions
   :members:
   :show-inheritance:

Pagination
--------------------------

.. automodule:: labelbox.pagination
   :members:
   :special-members: __init__
   :show-inheritance:

Enums
----------------------------

.. automodule:: labelbox.schema.enums
   :members:
   :show-inheritance:

ModelRun
----------------------------

.. automodule:: labelbox.schema.model_run
   :members:
   :show-inheritance:

Model
----------------------------

.. automodule:: labelbox.schema.model
   :members:
   :show-inheritance:

DataRowMetadata
----------------------------

.. automodule:: labelbox.schema.data_row_metadata
   :members:
   :exclude-members: _DeleteBatchDataRowMetadata
   :show-inheritance:

AnnotationImport
----------------------------

.. automodule:: labelbox.schema.annotation_import
   :members:
   :show-inheritance:

Batch
----------------------------

.. automodule:: labelbox.schema.batch
   :members:
   :show-inheritance:

ResourceTag
----------------------------

.. automodule:: labelbox.schema.resource_tag
   :members:
   :show-inheritance:


Slice
---------------------------
.. automodule:: labelbox.schema.slice
   :members:
   :show-inheritance:

QualityMode
-----------------------------------------
.. automodule:: labelbox.schema.quality_mode
   :members:
   :show-inheritance:

ExportTask
---------------------------
.. automodule:: labelbox.schema.export_task
   :members:
   :exclude-members: FileRetrieverByLine, FileRetrieverByOffset, FileRetrieverStrategy, Range, Converter
   :show-inheritance:

Identifiables
---------------------------
.. automodule:: labelbox.schema.identifiables
   :members:
   :show-inheritance:

Identifiable
---------------------------
.. automodule:: labelbox.schema.identifiable
   :members:
   :show-inheritance:

ConflictResolutionStrategy
---------------------------
.. automodule:: labelbox.schema.conflict_resolution_strategy
   :members:
   :show-inheritance:

FoundryClient
---------------------------
.. automodule:: labelbox.schema.foundry.foundry_client
   :members:
   :show-inheritance:

App
---------------------------
.. automodule:: labelbox.schema.foundry.app
   :members:
   :show-inheritance:

FoundryModel
---------------------------
.. automodule:: labelbox.schema.foundry.model
   :members:
   :show-inheritance:

SendToAnnotateParams
---------------------------
.. automodule:: labelbox.schema.send_to_annotate_params
   :members:
   :show-inheritance: