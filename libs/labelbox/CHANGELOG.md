# Changelog
# Version 5.0.0 (2024-09-16)
## Updated
* Set tasks_remaining_count to None LabelingServiceDashboard if labeling has not started ([#1817](https://github.com/Labelbox/labelbox-python/pull/1817))
* Improve error messaging when creating LLM project with invalid dataset id parameter([#1799](https://github.com/Labelbox/labelbox-python/pull/1799))
## Removed
* BREAKING CHANGE SDK methods for exports v1([#1800](https://github.com/Labelbox/labelbox-python/pull/1800))
* BREAKING CHANGE Unused labelbox_v1 serialization package([#1803](https://github.com/Labelbox/labelbox-python/pull/1803))
## Fixed
* Cuid dependencies that cause a crash if numpy is not installed ([#1807](https://github.com/Labelbox/labelbox-python/pull/1807))

# Version 4.0.0 (2024-09-10)
## Added
* BREAKING CHANGE for pydantic V1 users: Converted SDK to use pydantic V2([#1738](https://github.com/Labelbox/labelbox-python/pull/1738))
* Automation test support for multiple sdk versions([#1792](https://github.com/Labelbox/labelbox-python/pull/1792))
## Fixed
* Flaky tests([#1793](https://github.com/Labelbox/labelbox-python/pull/1793))

# Version 3.78.1 (2024-09-10)
## Fixed
* Labeling dashboard query for tags

# Version 3.78.0 (2024-09-03)
## Added
* Project get_labeling_service_dashboard() aka project detail (Miltiple PRs)
* Client get_labeling_service_dashboards() aka project list (Miltiple PRs)
* Client get_task_by_id()([#1767](https://github.com/Labelbox/labelbox-python/pull/1767))
* Support for MMC tasks annotations([#1787](https://github.com/Labelbox/labelbox-python/pull/1787))
## Fixed
* Build a test-pypi sdk instance even if tests fail([#1774](https://github.com/Labelbox/labelbox-python/pull/1774))

#  Version 3.77.1 (2024-08-28)
## Fixed
* Restore client.headers([#1781](https://github.com/Labelbox/labelbox-python/pull/1781))

#  Version 3.77.0 (2024-08-09)
## Added
* LabelingService request()([#1761](https://github.com/Labelbox/labelbox-python/pull/1761))
  * Validates all project requirements and requests a labeling service
* Allow marking Label with is_benchmark_reference flag([#1718](https://github.com/Labelbox/labelbox-python/pull/1718))
## Updated
* Project get_labeling_service() will now create labeling service if one is missing([#1762](https://github.com/Labelbox/labelbox-python/pull/1762))
## Removed
* **BREAKING CHANGE** Project.labeling_frontend.disconnect() ([#1763](https://github.com/Labelbox/labelbox-python/pull/1763))
  * We only support one default labeling front end per project and a user can not disconnect it
* **BREAKING CHANGE** Experimental method project.request_labeling_service() - duplicate, not needed([#1762](https://github.com/Labelbox/labelbox-python/pull/1762)).

#  Version 3.76.0 (2024-07-29)
# Added
* Added Project get_labeling_service(), request_labeling_service() and get_labeling_service_status()
* Added project and ontology creation for prompt response projects: Client create_prompt_response_generation_project(), create_response_creation_project() in https://github.com/Labelbox/labelbox-python/pull/1726
* Added is_benchmark_enabled, is_consensus_enabled to Project in https://github.com/Labelbox/labelbox-python/pull/1745

## Updated
* Made Project quality modes a list to allow combining more than 1 quality mode per project in https://github.com/Labelbox/labelbox-python/pull/1683

## Notebooks
* Added back in export migration guide in https://github.com/Labelbox/labelbox-python/pull/1736
* Added correct data param to video notebookin https://github.com/Labelbox/labelbox-python/pull/1732
NOTE: the notebooks will be removed and moved to this repo https://github.com/Labelbox/labelbox-notebooks soon

## Other
* Use connection pool for all http and graphql requests in https://github.com/Labelbox/labelbox-python/pull/1733

# Version 3.75.1 (2024-07-16)
## Removed
* Project MEDIA_TYPE JSON https://github.com/Labelbox/labelbox-python/pull/1728

# Version 3.75.0 (2024-07-10)
## Added
* Added Project set_project_model_setup_complete() method by @vbrodsky in https://github.com/Labelbox/labelbox-python/pull/1685
* Added user group management by @adrian-chang in https://github.com/Labelbox/labelbox-python/pull/1604
* Refactor Dataset create_data_rows_sync to use upsert by @vbrodsky in https://github.com/Labelbox/labelbox-python/pull/1694
* Added upload_type to Project by @vbrodsky in https://github.com/Labelbox/labelbox-python/pull/1707
* Added prompt classification for python object support by @Gabefire in https://github.com/Labelbox/labelbox-python/pull/1700
* Alias `wait_xxx` functions by @sfendell-labelbox in https://github.com/Labelbox/labelbox-python/pull/1675

## Fixed
* Predictions missing during Catalog slice Export by @adrian-chang in https://github.com/Labelbox/labelbox-python/pull/1695
* Prevented adding batches to live chat evaluation projects by @vbrodsky in https://github.com/Labelbox/labelbox-python/pull/1703
* Added missing media types by @adrian-chang in https://github.com/Labelbox/labelbox-python/pull/1705
* Deprecate Project setup_editor and add Project connect_ontology by @vbrodsky in https://github.com/Labelbox/labelbox-python/pull/1713
* Bumped dateutil max version by @colonelpanic8 in https://github.com/Labelbox/labelbox-python/pull/1716
* Bumped version rye by @adrian-chang in https://github.com/Labelbox/labelbox-python/pull/1719
* Updated create ontology for project setup by @vbrodsky in https://github.com/Labelbox/labelbox-python/pull/1722

## New Contributors
* @colonelpanic8 made their first contribution in https://github.com/Labelbox/labelbox-python/pull/1716

**Full Changelog**: https://github.com/Labelbox/labelbox-python/compare/v.3.74.0...v.3.75.0

# Version 3.74.0 (2024-06-24)
## Added
* Include predictions in export (#1689)
* Upsert label feedback method Client upsert_label_feedback() (#1684)

## Removed
* Removed deprecated class LabelList (#1691)

# Version 3.73.0 (2024-06-20)
## Added
* Conversational data row checks (#1678)
* UI ontology mode support (#1676)
* Empty data row validation (#1667)

## Fixed
* Numpy semver locked to < 2.0.0 (#1681)

# Changelog
# Version 3.72.2 (2024-06-10)
## Added
* SLSA provenance generation

# Version 3.72.1 (2024-06-06)
## Fixed
* Fix client.get_project() for LLM projects [PR #1658](https://github.com/Labelbox/labelbox-python/pull/1658)
* Throw user readable errors when creating a custom embedding [PR #1644](https://github.com/Labelbox/labelbox-python/pull/1644)

# Version 3.72.0 (2024-06-04)
## Added
* Update Dataset `create_data_rows` to allow upload of unlimited number of  data rows [PR #1627](https://github.com/Labelbox/labelbox-python/pull/1627), [PR #1648](https://github.com/Labelbox/labelbox-python/pull/1648)
* New Dataset methods for iam_integraton: `add_iam_integration`, `remove_iam_integration` [PR #1622](https://github.com/Labelbox/labelbox-python/pull/1622)

## Notebooks
* Added model evaluation SDK method notebook [PR #1645](https://github.com/Labelbox/labelbox-python/pull/1645)
* Added quick start notebook geared towards new users [PR #1640](https://github.com/Labelbox/labelbox-python/pull/1640)

# Version 3.71.0 (2024-05-28)
## Added
* `project.get_overview()` to be able to retrieve project details (#1615)
* `project.clone()` to be able to clone projects (#1624)
* Support for Rye 0.34 (#1625)
* Requirements.lock, Requirements-dev.lock to latest depdenencies (#1625)
* `ExportTask.get_buffered_stream` to replace `ExportTask.get_stream` (#1628)

## Fixed
* `ExportTask.result` / `ExportTask.errors` parsing content incorrectly (#1628)
* Lack of exceptions related to updating model config (#1634)

# Version 3.70.0 (2024-05-20)
## Added
* Added chat model evaluation support
  * client.create_model_config()
  * ModelConfig project_model_configs()
  * ModelConfig add_model_config()
  * ModelConfig delete_project_model_config()
  * ProjectModelConfig delete()
  * client.create_model_evaluation_project()
* Update existing methods to support chat model evaluation project
  * client.create_ontology()
  * client.create_ontology_from_feature_schemas()
* Coco deprecation message

## Fixed
* Fixed error reporting for client.create_project()
* Do not retry http 422 errors

## Notebooks
* Send_to_annotate_from_catalog functionalities outside Foundry

## Fixed in Notebooks
* Fixed meta notebook
* Modified queue_management.ipynb to remove some parameters
* Update_huggingface.ipynb
* Corrected_HF.ipynb

# Version 3.69.1 (2024-05-01)
## Fixed
* Fixed a bug with certain types of content not being returned as a result of `ExportTask.result` or `ExportTask.errors`

# Version 3.69.0 (2024-04-25)
## Added
* Support to export embeddings from the SDK

## Fixed
* Used OpenCV's headless library in replacement of OpenCV's default library

# Version 3.68.0 (2024-04-16)
## Added
* Added support for embeddings.
* Introduced the use of 'rye' as a package manager for SDK contributors.
* Implemented a unified 'create' method for AnnotationImport, MEAPredictionImport, and MALPredictionImport.
* Enhanced annotation upload functionality to accept data row IDs, global keys, or external IDs directly for labelbox.data.annotation_types.label

## Fixed
* Ensure items in dataset.upsert_data_rows are not empty
* Streamable export fix to report export_v2 errors as list of dictionaries, compatible with older releases

# Version 3.67.0 (2024-04-05)
## Added
* Added SECURITY.md file
* Made export_v2 methods use streamable backend
* Added support for custom embeddings to dataset _create data row(s)_ methods
* Added ability to upsert data rows via dataset.upsert_data_rows() method
* Added AssetAttachment with an ability to update() and delete()

## Updated
* Added check for 5000 labels per annotation per data row

## Fixed
* Errors and Failed data rows are included in the task.result for dataset.create_data_rows()
* Fixed 500 error handling and reporting 

# Notebooks
* Updated import notebook for image data
* Added attachment PDF example, removed requirements around text_layer_url
* Included the get_catalog() method to the export notebook 
* Added workflow status filter to export_data notebook for projects
* Send predictions to a project demo
* Removed model diagnostic notebooks

# Version 3.66.0 (2024-03-20)
## Notes

## Added
* Added support for Python 3.11, 3.12
* Added update method to attachments

## Notebooks
* Improved notebooks for integration and model diagnostics
* Removed databricks integrations notebooks

## Updated
* Updated README for clarity and contribution guidelines

## Removed
* Removed support Python 3.7 as it has been end of life since June 2023

# Version 3.65.0 (2024-03-05)
## Notes
* Rerelease of 3.64.0

# Version 3.64.0 (2024-02-29)

## Added
* `Client.get_catalog` Add catalog schema class. Catalog exports can now be made without creating a slice first
* `last_activity_at` filter added to export_v2, allowing users to specify a datetime window without a slice

## Removed
* Review related WebhookDataSource topics

## Notebooks
* Added get_catalog notebook
* Update custom metrics notebook
* Update notebooks for video and image annotation import

# Version 3.63.0 (2024-02-19)
## Added
* Ability for users to install and use sdk with pydantic v.2.* while still maintaining support for pydantic v1.*
* `ModelRun` `export()` and `export_v2()` add model_run_details to support splits

## Notebooks
* Add composite mask notebook

# Version 3.62.0 (2024-02-12)
## Added
* Support custom metrics for predictions (all applicable annotation classes)
* `FoundryClient.run_app` Add data_row identifier validation for running foundry app
* `Client.get_error_status_code` Default to 500 error if a server error is unparseable instead of throwing an exception

## Updated
* `DataRowMetadata, DataRowMetadataBatchResponse, _UpsertBatchDataRowMetadata` Make data_row_id and global_key optional in all schema types

## Fixed
* `ExportTask.__str__` Fix returned type in ExportTask instance representation

## Removed
* `Project.upsert_review_queue`

## Notebooks
* Update notebooks to new export methods
* Add model slice notebook
* Added support for annotation import with img bytes
* Update user prompts for huggingface colab

# Version 3.61.2 (2024-01-29)
## Added 
* `ModelSlice.get_data_row_identifiers` for Foundry data rows

## Fixed
* `ModelSlice.get_data_row_identifiers` scoping by model run id

# Version 3.61.1 (2024-01-25)
## Fixed
* Removed export API limit (5000)

# Version 3.61.0 (2024-01-22)
# Added
* `ModelSlice.get_data_row_identifiers`
  * Fetches all data row ids and global keys for the model slice
  * NOTE Foundry model slices are note supported yet
## Updated
* Updated exports v1 deprecation date to April 30th, 2024
* Remove `streamable` param from export_v2 methods

# Version 3.60.0 (2024-01-17)
## Added
* Get resource tags from a project
* Method to CatalogSlice to get data row identifiers (both uids and global keys)
* Added deprecation notice for the `upsert_review_queue` method in project
## Notebooks
* Update notebook for Project move_data_rows_to_task_queue
* Added notebook for model foundry
* Added notebook for migrating from Exports V1 to V2

# Version 3.59.0 (2024-01-05)
## Added
* Support set_labeling_parameter_overrides for global keys 
* Support bulk_delete of data row metadata for global keys
* Support bulk_export of data row metadata for global keys
## Fixed
* Stop overwriting class annotations on prediction upload
* Prevent users from uploading video annotations over the API limit (5000)
* Make description optional for foundry app
## Notebooks
* Update notebooks for Project set_labeling_parameter_overrides add support for global keys

# Version 3.58.1 (2023-12-15)
## Added
* Support to export all projects and all model runs to `export_v2` for a `dataset` and a `slice`
## Notebooks
* Update exports v2 notebook to include methods that return `ExportTask`

# Version 3.58.0 (2023-12-11)
## Added
* `ontology_id` to the model app instantiation
* LLM data generation label types
* `run_foundry_app` to support running model foundry apps
* Two methods for sending data rows to any workflow task in a project, that can also include predictions from a model run, or annotations from a different project
## Fixed
* Documentation index for identifiables
## Removed
* Project.datasets and Datasets.projects methods as they have been deprecated
## Notebooks
* Added note books for Human labeling(GT/MAL/MEA) + data generation (GT/MAL)
* Remove relationship annotations from text and conversational imports

# Version 3.57.0 (2023-11-30)
## Added
* Global key support for Project move_data_rows_to_task_queue
* Project name required for project creation
## Notebooks
* Updates to Image and Video notebook format
* Added additional byte array examples for Image/Video import and Image prediction import notebook
* Added a new LLM folder for new LLM import (MAL/MEA/Ground truth)

# Version 3.56.0 (2023-11-21)
## Added
* Support for importing raster video masks from image bytes as a source
* Add new ExportTask class to handle streaming of exports
## Fixed
* Check for empty fields during webhook creation
## Notebooks
* Updates to use bytes array for masks (video, image), and add examples of multiple notations per frame (video)

# Version 3.55.0 (2023-11-06)
## Fixed
* Fix the instantiation of `failed_data_row_ids` in Batch. This fix will address the issue with the `create_batch` method for more than 1,000 data rows.
* Improve Python type hints for the `data_rows()` method in the Dataset.
* Fix the `DataRowMetadataOntology` method `bulk_export()` to properly export global key(s).
* In the `DataRowMetadataOntology` method `update_enum_option`, provide a more descriptive error message when the enum option is not valid.

# Version 3.54.1 (2023-10-17)
## Notebooks
* Revised the notebooks to update outdated examples when using `client.create_project()` to create a project

# Version 3.54.0 (2023-10-10)
## Added
* Add exports v1 deprecation warning
* Create method in SDK to modify LPO priorities in bulk
## Removed
*  Remove backoff library

# Version 3.53.0 (2023-10-03)
## Added
* Remove LPO deprecation warning and allow greater range of priority values
* Add an sdk method to get data row by global key
* Disallow invalid quality modes during create_project
* Python 3.10 support
* Change return of dataset.create_data_rows() to Task
* Add new header to capture python version
## Notebooks
* Updated examples to match latest updates to SDK

# Version 3.52.0 (2023-08-24)
## Added
* Added methods to create multiple batches for a project from a list of data rows
* Limit the number of data rows to be checked for processing status

# Version 3.51.0 (2023-08-14)
## Added
* Added global keys to export v2 filters for project, dataset and DataRow
* Added workflow task status filtering for export v2

 ## Notebooks
* Removed labels notebook, since almost all of the relevant methods in the notebook were not compatible with workflow paradigm.
* Updated project.ipynb to use batches not datasets

# Version 3.50.0 (2023-08-04)
## Added
 * Support batch_ids filter for projects in Exports v2
 * Added access_from field to project members to differentiate project-based roles from organization level roles
 * Ability to use data_row_ids instead of the whole data row object for DataRow.export_V2()
 * Cursor-based pagination for dataset.data_rows()

 ## Fixed
 * client.get_projects() unable to fetch details for LLM projects

 ## Notebooks
 * Improved the documentation for `examples/basics/custom_embeddings.ipynb`
 * Updated the documentation for `examples/basics/data_row_metadata.ipynb`
 * Added details about CRUD methods to `examples/basics/ontologies.ipynb`

# Version 3.49.1 (2023-06-29)
## Fixed
* Removed numpy version lock that caused Python version >3.8 to download incompatible numpy version

# Version 3.49.0 (2023-06-27)

## Changed
* Improved batch creation logic when more than 1000 global keys provided

## Notebooks
* Added example on how to access mark in export v2
* Removed NDJSON library from `examples/basics/custom_embeddings.ipynb`
* Removed `queue_mode` property from `create_project()` method call.

# Version 3.48.0 (2023-06-13)
## Added
* Support for ISO format to exports V2 date filters
* Support to specify confidence for all free-text annotations

## Changed
* Removed backports library and replaced it with python dateutil package to parse iso strings

## Notebooks
* Added predictions to model run example
* Added notebook to run yolov8 and sam on video and upload to LB
* Updated google colab notebooks to reflect raster segmentation tool being released on 6/13
* Updated radio NDJSON annotations format to support confidence
* Added confidence to all free-text annotations (ndjson)
* Fixed issues with cv2 library rooting from the Geospatial notebook used a png map with a signed URL with an expired token

# Version 3.47.1 (2023-05-24)
## Fixed
* Loading of the ndjson parser when optional [data] libraries (geojson etc.) are not installed

# Version 3.47.0 (2023-05-23)
## Added
* Support for interpolated frames to export v2

## Changed
* Removed ndjson library and replaced it with a custom ndjson parser

## Notebooks
* Removed confidence scores in annotations - video notebook
* Removed raster seg masks from video prediction
* Added export v2 example
* Added SAM and Labelbox connector notebook

# Version 3.46.0 (2023-05-03)
## Added
* Global key support to DataRow Metadata `bulk_upsert()` function

## Notebooks
* Removed dataset based projects from project setup notebook
* Updated all links to annotation import and prediction notebooks in examples README

# Version 3.45.0 (2023-04-27)
## Changed
* Reduce threshold for async batch creation to 1000 data rows

## Notebooks
* Added subclassifications to ontology notebook
* Added conversational and pdf predictions notebooks

# Version 3.44.0 (2023-04-26)

## Added
* `predictions` param for optionally exporting predictions in model run export v2
* Limits on `model_run_ids` and `project_ids` on catalog export v2 params
* `WORKFLOW_ACTION` webhook topic
* Added `data_row_ids` filter for dataset and project export v2

## Fixed
* ISO timestamp parsing for datetime metadata
* Docstring typo for `client.delete_feature_schema_from_ontology()`

## Notebooks
* Removed mention of embeddings metadata fields
* Fixed broken colab link on `examples/extras/classification-confusion-matrix.ipynb`
* Added free text classification example to video annotation import notebook
* Updated prediction_upload notebooks with Annotation Type examples

# Version 3.43.0 (2023-04-05)

## Added
* Nested object classifications to `VideoObjectAnnotation`
* Relationship Annotation Types
* Added `project_ids` and `model_run_ids` to params in all export_v2 functions

## Fixed
* VideoMaskAnnotation annotation import

## Notebooks
* Added DICOM annotation import notebook
* Added audio annotation import notebook
* Added HTML annotation import notebook
* Added relationship examples to annotation import notebooks
* Added global video classification example
* Added nested classification examples
* Added video mask example
* Added global key and LPOs to queue management notebook

# Version 3.42.0 (2023-03-22)

## Added
* Message based classifications with annotation types for conversations
* Video and raster segmentation annotation types
* Global key support to `ConversationEntity`, `DocumentEntity` and `DicomSegments`
* DICOM polyline annotation type
* Confidence attribute to classification annotations

## Changed
* Increased metadata string size limit to 4096 chars
* Removed `deletedDataRowGlobalKey` from `get_data_row_ids_for_global_keys()`

## Fixed
* Annotation data type coercion by Pydantic
* Error message when end point coordinates are smaller than start point coordinates
* Some typos in error messages

## Notebooks
* Refactored video notebook to include annotation types
* Replaced data row ids with global keys in notebooks
* Replaced `create_data_row` with `create_data_rows` in notebooks

# Version 3.41.0 (2023-03-15)

## Added
* New data classes for creating labels: `AudioData`, `ConversationData`, `DicomData`, `DocumentData`, `HTMLData`
* New `DocumentEntity` annotation type class
* New parameter `last_activity_end` to `Project.export_labels()`

## Notebooks
* Updated `annotation_import/pdf.ipynb` with example use of `DocumentEntity` class

# Version 3.40.1 (2023-03-10)

## Fixed
* Fixed issue where calling create_batch() on exported data rows wasn't working

# Version 3.40.0 (2023-03-10)

## Added
* Support Global keys to reference data rows in `Project.create_batch()`, `ModelRun.assign_data_rows_to_split()`
* Support upserting labels via project_id in `model_run.upsert_labels()`
* `media_type_override` param to export_v2
* `last_activity_at` and `label_created_at` params to export_v2
* New client method `is_feature_schema_archived()`
* New client method `unarchive_feature_schema_node()`
* New client method `delete_feature_schema_from_ontology()`

## Changed
* Removed default task names for export_v2

## Fixed
* process_label() for COCO panoptic dataset

## Notebooks
* Updated `annotation_import/pdf.ipynb` with more examples
* Added `integrations/huggingface/huggingface.ipynb`
* Fixed broken links for detectron notebooks in README
* Added Dataset QueueMode during project creation in `integrations/detectron2/coco_object.ipynb`
* Removed metadata and updated ontology in `annotation_import/text.ipynb`
* Removed confidence scores in `annotation_import/image.ipynb`
* Updated custom embedding tutorial links in `basics/data_row_metadata.ipynb`

# Version 3.39.0 (2023-02-28)
## Added
* New method `Project.task_queues()` to obtain the task queues for a project.
* New method `Project.move_data_rows_to_task_queue()` for moving data rows to a specified task queue.
* Added more descriptive error messages for metadata operations
* Added `Task.errors_url` for async tasks that return errors as separate file (e.g. `export_v2`)
* Upsert data rows to model runs using global keys

## Changed
* Updated `ProjectExportParams.labels` to `ProjectExportParams.label_details`
* Removed `media_attributes` from `DataRowParams`
* Added deprecation warnings for `LabelList` and removed its usage
* Removed unused arguments in `Project.export_v2` and `ModelRun.export_v2`
* In `Project.label_generator()`, we now filter skipped labels for project with videos

## Notebooks
* Fixed `examples/label_export/images.ipynb` notebook metadata
* Removed unused `lb_serializer` imports
* Removed uuid generation in NDJson annotation payloads, as it is now optional
* Removed custom embeddings usage in `examples/basics/data_row_metadata.ipynb`
* New notebook `examples/basics/custom_embeddings.ipynb` for custom embeddings
* Updated `examples/annotation_import/text.ipynb` to use `TextData` and specify Text media type

# Version 3.38.0 (2023-02-15)

## Added
* All imports are available via `import labelbox as lb` and `import labelbox.types as lb_types`.
* Attachment_name support to create_attachment()

## Changed
* `LabelImport.create_from_objects()`, `MALPredictionImport.create_from_objects()`, `MEAPredictionImport.create_from_objects()`, `Project.upload_annotations()`, `ModelRun.add_predictions()` now support Python Types for annotations.

## Notebooks
* Removed NDJsonConverter from example notebooks
* Simplified imports in all notebooks
* Fixed nested classification in examples/annotation_import/image.ipynb
* Ontology (instructions --> name)

# Version 3.37.0 (2023-02-08)
## Added
* New `last_activity_start` param to `project.export_labels()` for filtering which labels are exported. See docstring for more on how this works.

## Changed
* Rename `Classification.instructions` to `Classification.name`

## Fixed
* Retry connection timeouts

# Version 3.36.1 (2023-01-24)
### Fixed
* `confidence` is now optional for TextEntity

# Version 3.36.0 (2023-01-23)
### Fixed
* `confidence` attribute is now supported for TextEntity and Line predictions

# Version 3.35.0 (2023-01-18)
### Fixed
* Retry 520 errors when uploading files

# Version 3.34.0 (2022-12-22)
### Added
* Added `get_by_name()` method to MetadataOntology object to access both custom and reserved metadata by name.
* Added support for adding metadata by name when creating datarows using `DataRowMetadataOntology.bulk_upsert()`.
* Added support for adding metadata by name when creating datarows using `Dataset.create_data_rows()`, `Dataset.create_data_rows_sync()`, and `Dataset.create_data_row()`.
* Example notebooks for auto metrics in models

### Changed
* `Dataset.create_data_rows()` max limit of DataRows increased to 150,000
* Improved error handling for invalid annotation import content
* String metadata can now be 1024 characters long (from 500)

## Fixed
* Broken urls in detectron notebook

# Version 3.33.1 (2022-12-14)
### Fixed
* Fixed where batch creation limit was still limiting # of data rows. SDK should now support creating batches with up to 100k data rows

# Version 3.33.0 (2022-12-13)
### Added
* Added SDK support for creating batches with up to 100k data rows
* Added optional media_type to `client.create_ontology_from_feature_schemas()` and `client.create_ontology()`

### Changed
* String representation of `DbObject` subclasses are now formatted

# Version 3.32.0 (2022-12-02)
### Added
* Added `HTML` Enum to `MediaType`. `HTML` is introduced as a new asset type in Labelbox.
* Added `PaginatedCollection.get_one()` and `PaginatedCollection.get_many()` to provide easy functions to fetch single and bulk instances of data for any function returning a `PaginatedCollection`. E.g. `data_rows = dataset.data_rows().get_many(10)`
* Added a validator under `ScalarMetric` to validate metric names against reserved metric names

### Changed
* In `iou.miou_metric()` and `iou.feature_miou_metric`, iou metric renamed as `custom_iou`

# Version 3.31.0 (2022-11-28)
### Added
* Added `client.clear_global_keys()` to remove global keys from their associated data rows
* Added a new attribute `confidence` to `AnnotationObject` and `ClassificationAnswer` for Model Error Analysis

### Fixed
* Fixed `project.create_batch()` to work with both data_row_ids and data_row objects

# Version 3.30.1 (2022-11-16)
### Added
* Added step to `project.create_batch()` to wait for data rows to finish processing
### Fixed
* Running `project.setup_editor()` multiple times no longer resets the ontology, and instead raises an error if the editor is already set up for the project

# Version 3.30.0 (2022-11-11)
### Changed
* create_data_rows, create_data_rows_sync, create_data_row, and update data rows all accept the new data row input format for row data
* create_data_row now accepts an attachment parameter to be consistent with create_data_rows
* Conversational text data rows will be uploaded to a json file automatically on the backend to reduce the amount of i/o required in the SDK.

# Version 3.29.0 (2022-11-02)
### Added
* Added new base `Slice` Entity/DbObject and `CatalogSlice` class
* Added `client.get_catalog_slice(id)` to fetch a CatalogSlice by ID
* Added `slice.get_data_row_ids()` to fetch data row ids of the slice
* Add deprecation warning for queue_mode == QueueMode.Dataset when creating a new project.
* Add deprecation warning for LPOs.

### Changed
* Default behavior for metrics to not include subclasses in the calculation.

### Fixed
* Polygon extraction from masks creating invalid polygons. This would cause issues in the coco converter.

# Version 3.28.0 (2022-10-14)

### Added
* Added warning for upcoming change in default project queue_mode setting
* Added notebook example for importing Conversational Text annotations using Model-Assisted Labeling

### Changed
* Updated QueueMode enum to support new value for QueueMode.Batch = `BATCH`.
* Task.failed_data_rows is now a property

### Fixed
* Fixed Task.wait_till_done() showing warning message for every completed task, instead of only warning when task has errors
* Fixed error on dataset creation step in examples/annotation_import/video.ipynb notebook

# Version 3.27.2 (2022-10-04)

### Added
* Added deprecation warning for missing `media_type` in `create_project` in `Client`.

### Changed
* Updated docs for deprecated methods `_update_queue_mode` and `get_queue_mode` in `Project`
    * Use the `queue_mode` attribute in `Project` to get and set the queue mode instead
    * For more information, visit https://docs.labelbox.com/reference/migrating-to-workflows#upcoming-changes
* Updated `project.export_labels` to support filtering by start/end time formats "YYYY-MM-DD" and "YYYY-MM-DD hh:mm:ss"

### Fixed

# Version 3.27.1 (2022-09-16)
### Changed
* Removed `client.get_data_rows_for_global_keys` until further notice

# Version 3.27.0 (2022-09-12)
### Added
* Global Keys for data rows
    * Assign global keys to a data row with `client.assign_global_keys_to_data_rows`
    * Get data rows using global keys with `client.get_data_row_ids_for_global_keys` and `client.get_data_rows_for_global_keys`
* Project Creation
    * Introduces `Project.queue_mode` as an optional parameter when creating projects
* `MEAToMALPredictionImport` class
    * This allows users to use predictions stored in Models for MAL
* `Task.wait_till_done` now shows a warning if task has failed
### Changed
* Increase scalar metric value limit to 100m
* Added deprecation warnings when updating project `queue_mode`
### Fixed
* Fix bug in `feature_confusion_matrix` and `confusion_matrix` causing FPs and FNs to be capped at 1 when there were no matching annotations

# Version 3.26.2 (2022-09-06)
### Added
* Support for document (pdf) de/serialization from exports
    * Use the `LBV1Converter.serialize()` and `LBV1Converter.deserialize()` methods
* Support for document (pdf) de/serialization for imports
    * Use the `NDJsonConverter.serialize()` and `NDJsonConverter.deserialize()` methods

# Version 3.26.1 (2022-08-23)
### Changed
* `ModelRun.get_config()`
    * Modifies get_config to return un-nested Model Run config
### Added
* `ModelRun.update_config()`
    * Updates model run training metadata
* `ModelRun.reset_config()`
    * Resets model run training metadata
* `ModelRun.get_config()`
    * Fetches model run training metadata

### Changed
* `Model.create_model_run()`
    * Add training metadata config as a model run creation param

# Version 3.26.0 (2022-08-15)
## Added
* `Batch.delete()` which will delete an existing `Batch`
* `Batch.delete_labels()`  which will delete all `Label`’s created after a `Project`’s mode has been set to batch.
    * Note: Does not include labels that were imported via model-assisted labeling or label imports
* Support for creating model config when creating a model run
* `RAW_TEXT` and `TEXT_FILE` attachment types to replace the `TEXT` type.

# Version 3.25.3 (2022-08-10)
## Fixed
* Label export will continue polling if the downloadUrl is None

# Version 3.25.2 (2022-07-26)
## Updated
* Mask downloads now have retries
* Failed `upload_data` now shows more details in the error message

## Fixed
* Fixed Metadata not importing with DataRows when bulk importing local files.
* Fixed COCOConverter failing for empty annotations

## Documentation
* Notebooks are up-to-date with examples of importing annotations without `schema_id`

# Version 3.25.1 (2022-07-20)
## Fixed
* Removed extra dependency causing import errors.

# Version 3.25.0 (2022-07-20)

## Added
* Importing annotations with model assisted labeling or label imports using ontology object names instead of schemaId now possible
    * In Python dictionaries, you can now use `schemaId` key or `name` key for all tools, classifications, options
* Labelbox's Annotation Types now support model assisted labeling or label imports using ontology object names
* Export metadata when using the following methods:
    * `Batch.export_data_rows(include_metadata=True)`
    * `Dataset.export_data_rows(include_metadata=True)`
    * `Project.export_queued_data_rows(include_metadata=True)`
* `VideoObjectAnnotation` has `segment_index` to group video annotations into video segments

## Removed
* `Project.video_label_generator`. Use `Project.label_generator` instead.

## Updated
* Model Runs now support unassigned splits
* `Dataset.create_data_rows` now has the following limits:
    * 150,000 rows per upload without metadata
    * 30,000 rows per upload with metadata


# Version 3.24.1 (2022-07-07)
## Updated
* Added `refresh_ontology()` as part of create/update/delete metadata schema functions

# Version 3.24.0 (2022-07-06)
## Added
* `DataRowMetadataOntology` class now has functions to create/update/delete metadata schema
    * `create_schema` - Create custom metadata schema
    * `update_schema` - Update name of custom metadata schema
    * `update_enum_options` - Update name of an Enum option for an Enum custom metadata schema
    * `delete_schema` - Delete custom metadata schema
* `ModelRun` class now has `assign_data_rows_to_split` function, which can assign a `DataSplit` to a list of `DataRow`s
* `Dataset.create_data_rows()` can bulk import `conversationalData`

# Version 3.23.3 (2022-06-23)

## Fix
* Import for `numpy` has been adjusted to work with numpy v.1.23.0

# Version 3.23.2 (2022-06-15)
## Added
* `Data Row` object now has a new field, `metadata`, which returns metadata associated with data row as a list of `DataRowMetadataField`
    * Note: When importing Data Rows with metadata, use the existing field, `metadata_fields`

# Version 3.23.1 (2022-06-08)
## Added
* `Task` objects now have the following properties:
    * `errors` - fetch information about why the task failed
    * `result` - fetch the result of the task
    * These are currently only compatible with data row import tasks.
* Officially added support for python 3.9

## Removed
* python 3.6 is no longer officially supported

# Version 3.22.1 (2022-05-23)
## Updated
* Renamed `custom_metadata` to `metadata_fields` in DataRow

# Version 3.22.0 (2022-05-20)
## Added
* `Dataset.create_data_row()` and `Dataset.create_data_rows()` now uploads metadata to data row
* Added `media_attributes` and `metadata` to `BaseData`

## Updated
* Removed `iou` from classification metrics

# Version 3.21.1 (2022-05-12)
## Updated
  * `Project.create_batch()` timeout increased to 180 seconds

# Version 3.21.0 (2022-05-11)
## Added
  * Projects can be created with a `media_type`
  * Added `media_type` attribute to `Project`
  * New `MediaType` enumeration

## Fix
  * Added back the mimetype to datarow bulk uploads for orgs that require delegated access

# Version 3.20.1 (2022-05-02)
## Updated
* Ontology Classification `scope` field is only set for top level classifications

# Version 3.20.0 (2022-04-27)
## Added
* Batches in a project can be retrieved with `project.batches()`
* Added `Batch.remove_queued_data_rows()` to cancel remaining data rows in batch
* Added `Batch.export_data_rows()` which returns `DataRow`s for a batch

## Updated
* NDJsonConverter now supports Video bounding box annotations.
    * Note: Currently does not support nested classifications.
    * Note: Converting an export into Labelbox annotation types, and back to export will result in only keyframe annotations. This is to support correct import format.


## Fix
* `batch.project()` now works

# Version 3.19.1 (2022-04-14)
## Fix
* `create_data_rows` and `create_data_rows_sync` now uploads the file with a mimetype
* Orgs that only allow DA uploads were getting errors when using these functions

# Version 3.19.0 (2022-04-12)
## Added
* Added Tool object type RASTER_SEGMENTATION for Video and DICOM ontologies

# Version 3.18.0 (2022-04-07)
## Added
* Added beta support for exporting labels from model_runs
* LBV1Converter now supports data_split key
* Classification objects now include `scope` key

## Fix
* Updated notebooks

# Version 3.17.2 (2022-03-28)
## Fix
* Project.upsert_instructions now works properly for new projects.

# Version 3.17.1 (2022-03-25)
## Updated
* Remove unused rasterio dependency

# Version 3.17.0 (2022-03-22)
## Added
* Create batches from the SDK (Beta). Learn more about [batches](https://docs.labelbox.com/docs/batches)
* Support for precision and recall metrics on Entity annotations

## Fix
* `client.create_project` type hint added for its return type

## Updated
* Removed batch MVP code

# Version 3.16.0 (2022-03-08)
## Added
* Ability to fetch a model run with `client.get_model_run()`
* Ability to fetch labels from a model run with `model_run.export_labels()`
    - Note: this is only Experimental. To use, client param `enable_experimental` should
    be set to true
* Ability to delete an attachment

## Fix
* Logger level is no longer set to INFO

## Updated
* Deprecation: Creating Dropdowns will no longer be supported after 2022-03-31
    - This includes creating/adding Dropdowns to an ontology
    - This includes creating/adding Dropdown Annotation Type
    - For the same functionality, use Radio
    - This will not affect existing Dropdowns

# Changelog
# Version 3.15.0 (2022-02-28)
## Added
* Extras folder which contains useful applications using the sdk
* Addition of ResourceTag at the Organization and Project level
* Updates to the example notebooks

## Fix
* EPSGTransformer now properly transforms Polygon to Polygon
* VideoData string representation now properly shows VideoData


# Version 3.14.0 (2022-02-10)
## Added
* Updated metrics for classifications to be per-answer


# Version 3.13.0 (2022-02-07)
## Added
* Added `from_shapely` method to create annotation types from Shapely objects
* Added `start` and `end` filter on the following methods
- `Project.export_labels()`
- `Project.label_generator()`
- `Project.video_label_generator()`
* Improved type hinting


# Version 3.12.0 (2022-01-19)
## Added
* Tiled Imagery annotation type
- A set of classes that support Tiled Image assets
- New demo notebook can be found here: examples/annotation_types/tiled_imagery_basics.ipynb
- Updated tiled image mal can be found here: examples/model_assisted_labeling/tiled_imagery_mal.ipynb
* Support transformations from one EPSG to another with `EPSGTransformer` class
- Supports EPSG to Pixel space transformations


# Version 3.11.1 (2022-01-10)
## Fix
* Make `TypedArray` class compatible with `numpy` versions `>= 1.22.0`
* `project.upsert_review_queue` quotas can now be in the inclusive range [0,1]
* Restore support for upserting html instructions to a project

# Version 3.11.0 (2021-12-15)

## Fix
* `Dataset.create_data_rows()` now accepts an iterable of data row information instead of a list
* `project.upsert_instructions()`
    * now only supports pdfs since that is what the editor requires
    * There was a bug that could cause this to modify the project ontology

## Removed
* `DataRowMetadataSchema.id` use `DataRowMetadataSchema.uid` instead
* `ModelRun.delete_annotation_groups()` use `ModelRun.delete_model_run_data_rows()` instead
* `ModelRun.annotation_groups()` use `ModelRun.model_run_data_rows()` instead

# Version 3.10.0 (2021-11-18)
## Added
* `AnnotationImport.wait_until_done()` accepts a `show_progress` param. This is set to `False` by default.
    * If enabled, a tqdm progress bar will indicate the import progress.
    * This works for all classes that inherit from AnnotationImport: `LabelImport`, `MALPredictionImport`, `MEAPredictionImport`
    * This is not support for `BulkImportRequest` (which will eventually be replaced by `MALPredictionImport`)
* `Option.label` and `Option.value` can now be set independently
* `ClassificationAnswer`s now support a new `keyframe` field for videos
* New `LBV1Label.media_type field. This is a placeholder for future backend changes.

## Fix
* Nested checklists can have extra brackets. This would cause the annotation type converter to break.


# Version 3.9.0 (2021-11-12)
## Added
* New ontology management features
    * Query for ontologies by name with `client.get_ontologies()` or by id using `client.get_ontology()`
    * Query for feature schemas by name with `client.get_feature_schemas()` or id using `client.get_feature_schema()`
    * Create feature schemas with `client.create_feature_schemas()`
    * Create ontologies from normalized ontology data with `client.create_ontology()`
    * Create ontologies from feature schemas with `client.create_ontology_from_feature_schemas()`
    * Set up a project from an existing ontology with `project.setup_edior()`
    * Added new `FeatureSchema` entity
* Add support for new queue modes
    * Send batches of data directly to a project queue with `project.queue()`
    * Remove items from a project queue with `project.dequeue()`
    * Query for and toggle the queue mode

# Version 3.8.0 (2021-10-22)
## Added
* `ModelRun.upsert_data_rows()`
    * Add data rows to a model run without also attaching labels
* `OperationNotAllowedException`
    * raised when users hit resource limits or are not allowed to use a particular operation

## Updated
* `ModelRun.upsert_labels()`
    * Blocks until the upsert job is complete. Error messages have been improved
* `Organization.invite_user()` and `Organization.invite_limit()` are no longer experimental
* `AnnotationGroup` was renamed to `ModelRunDataRow`
* `ModelRun.delete_annotation_groups()` was renamed to `ModelRun.delete_model_run_data_rows()`
* `ModelRun.annotation_groups()` was renamed to `ModelRun.model_run_data_rows()`

## Fix
* `DataRowMetadataField` no longer relies on pydantic for field validation and coercion
    * This prevents unintended type coercions from occurring

# Version 3.7.0 (2021-10-11)
## Added
* Search for data row ids from external ids without specifying a dataset
    * `client.get_data_row_ids_for_external_ids()`
* Support for numeric metadata type

## Updated
* The following `DataRowMetadataOntology` fields were renamed:
    * `all_fields` -> `fields`
    * `all_fields_id_index` -> `fields_by_id`
    * `reserved_id_index` -> `reserved_by_id`
    * `reserved_name_index` -> `reserved_by_name`
    * `custom_id_index` -> `custom_by_id`
    * `custom_name_index` -> `custom_by_name`


# Version 3.6.1 (2021-10-07)
* Fix import error that appears when exporting labels

# Version 3.6.0 (2021-10-04)
## Added
* Bulk export metadata with `DataRowMetadataOntology.bulk_export()`
* Add docstring examples of annotation types and a few helper methods

## Updated
* Update metadata notebook under examples/basics to include bulk_export.
* Allow color to be a single integer when constructing Mask objects
* Allow users to pass int arrays to RasterData and attempt coercion to uint8

## Removed
* data_row.metadata was removed in favor of bulk exports.


# Version 3.5.0 (2021-09-15)
## Added
* Diagnostics custom metrics
    * Metric annotation types
    * Update ndjson converter to be compatible with metric types
    * Metric library for computing confusion matrix metrics and iou
    * Demo notebooks under `examples/diagnostics`
* COCO Converter
* Detectron2 example integration notebooks

# Version 3.4.1 (2021-09-10)
## Fix
* Iam validation exception message

# Version 3.4.0 (2021-09-10)
## Added
* New `IAMIntegration` entity
* `Client.create_dataset()` compatibility with delegated access
* `Organization.get_iam_integrations()` to list all integrations available to an org
* `Organization.get_default_iam_integration()` to only get the defaault iam integration

# Version 3.3.0 (2021-09-02)
## Added
* `Dataset.create_data_rows_sync()` for synchronous bulk uploads of data rows
* `Model.delete()`, `ModelRun.delete()`, and `ModelRun.delete_annotation_groups()` to
    Clean up models, model runs, and annotation groups.

## Fix
* Increased timeout for label exports since projects with many segmentation masks weren't finishing quickly enough.

# Version 3.2.1 (2021-08-31)
## Fix
* Resolved issue with `create_data_rows()` was not working on amazon linux

# Version 3.2.0 (2021-08-26)
## Added
* List `BulkImportRequest`s for a project with `Project.bulk_import_requests()`
* Improvemens to `Dataset.create_data_rows()`
    * Add attachments when bulk importing data rows
    * Provide external ids when creating data rows from local files
    * Get more informative error messages when the api rejects an import

## Fix
* Bug causing `project.label_generator()` to fail when projects had benchmarks

# Version 3.1.0 (2021-08-18)
## Added
* Support for new HTML attachment type
* Delete Bulk Import Requests with `BulkImportRequest.delete()`

## Misc
* Updated MEAPredictionImport class to use latest grapqhql endpoints


# Version 3.0.1 (2021-08-12)
## Fix
* Issue with inferring text type from export

# Version 3.0.0 (2021-08-12)
## Added
* Annotation types
    - A set of python objects for working with labelbox data
    - Creates a standard interface for both exports and imports
    - See example notebooks on how to use under examples/annotation_types
    - Note that these types are not yet supported for tiled imagery
* MEA Support
    - Beta MEA users can now just use the latest SDK release
* Metadata support
    - New metadata features are now fully supported by the SDK
* Easier export
    - `project.export_labels()` accepts a boolean indicating whether or not to download the result
    - Create annotation objects directly from exports with `project.label_generator()` or `project.video_label_generator()`
    - `project.video_label_generator()` asynchronously fetches video annotations
* Retry logic on data uploads
    - Bulk creation of data rows will be more reliable
* Datasets
    - Determine the number of data rows just by calling `dataset.row_count`.
    - Updated threading logic in create_data_rows() to make it compatible with aws lambdas
* Ontology
    - `OntologyBuilder`, `Classification`, `Option`, and `Tool` can now be imported from `labelbox` instead of `labelbox.schema.ontology`

## Removed
* Deprecated:
    - `project.reviews()`
    - `project.create_prediction()`
    - `project.create_prediction_model()`
    - `project.create_label()`
    - `Project.predictions()`
    - `Project.active_prediction_model`
    - `data_row.predictions`
    - `PredictionModel`
    - `Prediction`
* Replaced:
    - `data_row.metadata()` use `data_row.attachments()` instead
    - `data_row.create_metadata()` use `data_row.create_attachments()` instead
    - `AssetMetadata` use `AssetAttachment` instead

## Fixes
* Support derived classes of ontology objects when using `from_dict`
* Notebooks:
    - Video export bug where the code would fail if the exported projects had tools other than bounding boxes
    - MAL demos were broken due to an image download failing.

## Misc
* Data processing dependencies are not installed by default to for users that only want client functionality.
* To install all dependencies required for the data modules (annotation types and mea metric calculation) use `pip install labelbox[data]`
* Decrease wait time between updates for `BulkImportRequest.wait_until_done()`.
* Organization is no longer used to create the LFO in `Project.setup()`


# Version 3.0.0-rc3 (2021-08-11)
## Updates
* Geometry.raster now has a consistent interface and improved functionality
* renamed schema_id to feature_schema_id in the `FeatureSchema` class
* `Mask` objects now use `MaskData` to represent segmentation masks instead of `ImageData`

# Version 3.0.0-rc2 (2021-08-09)
## Updates
* Rename `data` property of TextData, ImageData, and VideoData types to `value`.
* Decrease wait time between updates for `BulkImportRequest.wait_until_done()`
* Organization is no longer used to create the LFO in `Project.setup()`


# Version 3.0.0-rc1 (2021-08-05)
## Added
* Model diagnostics notebooks
* Minor annotation type improvements

# Version 3.0.0-rc0 (2021-08-04)
## Added
* Annotation types
    - A set of python objects for working with labelbox data
    - Creates a standard interface for both exports and imports
    - See example notebooks on how to use under examples/annotation_types
    - Note that these types are not yet supported for tiled imagery
* MEA Support
    - Beta MEA users can now just use the latest SDK release
* Metadata support
    - New metadata features are now fully supported by the SDK
* Easier export
    - `project.export_labels()` accepts a boolean indicating whether or not to download the result
    - Create annotation objects directly from exports with `project.label_generator()` or `project.video_label_generator()`
    - `project.video_label_generator()` asynchronously fetches video annotations
* Retry logic on data uploads
    - Bulk creation of data rows will be more reliable
* Datasets
    - Determine the number of data rows just by calling `dataset.row_count`.
    - Updated threading logic in create_data_rows() to make it compatible with aws lambdas
* Ontology
    - `OntologyBuilder`, `Classification`, `Option`, and `Tool` can now be imported from `labelbox` instead of `labelbox.schema.ontology`

## Removed
* Deprecated:
    - `project.reviews()`
    - `project.create_prediction()`
    - `project.create_prediction_model()`
    - `project.create_label()`
    - `Project.predictions()`
    - `Project.active_prediction_model`
    - `data_row.predictions`
    - `PredictionModel`
    - `Prediction`
* Replaced:
    - `data_row.metadata()` use `data_row.attachments()` instead
    - `data_row.create_metadata()` use `data_row.create_attachments()` instead
    - `AssetMetadata` use `AssetAttachment` instead

## Fixes
* Support derived classes of ontology objects when using `from_dict`
* Notebooks:
    - Video export bug where the code would fail if the exported projects had tools other than bounding boxes
    - MAL demos were broken due to an image download failing.

## Misc
* Data processing dependencies are not installed by default to for users that only want client functionality.
* To install all dependencies required for the data modules (annotation types and mea metric calculation) use `pip install labelbox[data]`

# Version 2.7b1+mea (2021-06-27)
## Fix
* No longer convert `ModelRun.created_by_id` to cuid on construction of a `ModelRun`.
    * This was causing queries for ModelRuns to fail.

# Version 2.7b0+mea (2021-06-27)
## Fix
* Update `AnnotationGroup` to expect labelId to be a cuid instead of uuid.
* Update `datarow_miou` to support masks with multiple classes in them.

# Version 2.7.0 (2021-06-27)
## Added
* Added `dataset.export_data_rows()` which returns all `DataRows` for a `Dataset`.

# Version 2.6b2+mea (2021-06-16)
## Added
* `ModelRun.annotation_groups()` to fetch data rows and label information for a model run

# Version 2.6.0 (2021-06-11)
## Fix
* Upated `create_mask_ndjson` helper function in `image_mal.ipynb` to use the color arg
    instead of a hardcoded color.

## Added
* asset_metadata is now deprecated and has been replaced with asset_attachments
    * `AssetAttachment` replaces `AssetMetadata` ( see definition for updated attribute names )
    * Use `DataRow.attachments()` instead of `DataRow.metadata()`
    * Use `DataRow.create_attachment()` instead of `DataRow.create_metadata()`
* Update pydantic version

# Version 2.5b0+mea (2021-06-11)
## Added
* Added new `Model` and 'ModelRun` entities
* Update client to support creating and querying for `Model`s
* Implement new prediction import pipeline to support both MAL and MEA
* Added notebook to demonstrate how to use MEA
* Added `datarow_miou` for calculating datarow level iou scores


# Version 2.5.6 (2021-05-19)
## Fix
* MAL validation no longer raises exception when NER tool has same start and end location

# Version 2.5.5 (2021-05-17)
## Added
* `DataRow` now has a `media_attributes` field
* `DataRow`s can now be looked up from `LabelingParameterOverride`s
* `Project.export_queued_data_rows` to export all data rows in a queue for a project at once

# Version 2.5.4 (2021-04-22)
## Added
* User management
    * Query for remaining invites and users available to an organization
    * Set and update organization roles
    * Set / update / revoke project role
    * Delete users from organization
    * Example notebook added under examples/basics
* Issues and comments export
    * Bulk export issues and comments. See `Project.export_issues`
* MAL on Tiled Imagery
    * Example notebook added under examples/model_assisted_labeling
    * `Dataset.create_data_rows` now allows users to upload tms imagery

# Version 2.5.3 (2021-04-01)
## Added
* Cleanup and add additional example notebooks
* Improved README for SDK and examples
* Easier to retrieve per annotation `BulkImportRequest` status, errors, and inputs
    * See `BulkImportRequest.errors`, `BulkImportRequest.statuses`, `BulkImportRequest.inputs` for more information

# Version 2.5.2 (2021-03-25)
## Fix
* Ontology builder defaults to None for missing fields instead of empty lists
* MAL validation added extra fields to subclasses

### Added
* Example notebooks

## Version 2.5.1 (2021-03-15)
### Fix
* `Dataset.data_row_for_external_id` No longer throws `ResourceNotFoundError` when there are duplicates
*  Improved doc strings

### Added
* OntologyBuilder for making project setup easier
* Now supports `IMAGE_OVERLAY` metadata
* Webhooks for review topics added
* Upload project instructions with `Project.upsert_instructions`
* User input validation
    * MAL validity is now checked client side for faster feedback
    * type and value checks added in a few places

## Version 2.4.11 (2021-03-07)
### Fix
* Increase query timeout
* Retry 502s

## Version 2.4.10 (2021-02-05)
### Added
* SDK version added to request headers

## Version 2.4.9 (2020-11-09)
### Fix
* 2.4.8 was broken for > Python 3.6
### Added
* include new `Project.enable_model_assisted_labeling` method for turning on [model-assisted labeling](https://labelbox.com/docs/automation/model-assisted-labeling)

## Version 2.4.8 (2020-11-06)
### Fix
* fix failing `next` call https://github.com/Labelbox/labelbox-python/issues/74

## Version 2.4.7 (2020-09-10)
### Added
* `Ontology` schema for interacting with ontologies and their schema nodes

## Version 2.4.6 (2020-09-03)
### Fix
* fix failing `create_metadata` calls

## Version 2.4.5 (2020-09-01)
### Added
* retry capabilities for common flaky API failures
* protection against improper types passed into `Project.upload_anntations`
* pass thru API error messages when possible

## Version 2.4.3 (2020-08-04)

### Added
* `BulkImportRequest` data type
* `Project.upload_annotation` supports uploading via a local ndjson file, url, or a iterable of annotations

## Version 2.4.2 (2020-08-01)
### Fixed
* `Client.upload_data` will now pass the correct `content-length` when uploading data.

## Version 2.4.1 (2020-07-22)
### Fixed
* `Dataset.create_data_row` and `Dataset.create_data_rows` will now upload with content type to ensure the Labelbox editor can show videos.

## Version 2.4 (2020-01-30)

### Added
* `Prediction` and `PredictionModel` data types.

## Version 2.3 (2019-11-12)

### Changed
* `Client.execute` now automatically extracts the 'data' value from the
returned `dict`. This *breaks* existing code that directly uses the
`Client.execute` method.
* Major code reorganization, naming and test improvements.
* `Label.seconds_to_label` field value is now optional when creating
a `Label`. Default value is 0.0.

### Added
* `Project.upsert_review_queue` method.
* `Project.extend_reservations` method.
* `Label.created_by` relationship (To-One User).
* Changelog.

### Fixed
* `Dataset.create_data_row` upload of local file data.

## Version 2.2 (2019-10-18)
Changelog not maintained before version 2.2.
