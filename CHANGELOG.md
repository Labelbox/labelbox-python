# Changelog

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
