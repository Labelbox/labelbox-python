# Changelog

## Unreleased

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
