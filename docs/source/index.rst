Labelbox Python API reference
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Client
----------------------

.. automodule:: labelbox.client
   :members:
   :special-members: __init__
   :exclude-members: upload_data, upload_file
   :show-inheritance:

AssetMetadata
--------------------------------------

.. automodule:: labelbox.schema.asset_metadata
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

Prediction
---------------------------------

.. automodule:: labelbox.schema.prediction
   :members: Prediction
   :exclude-members: PredictionModel
   :show-inheritance:

PredictionModel
---------------------------------
.. automodule:: labelbox.schema.prediction
    :members: PredictionModel
    :exclude-members: Prediction
    :show-inheritance:
    :noindex:

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

