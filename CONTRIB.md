# Labelbox Python SDK Contribution Guide

## Repository Organization

The SDK source (excluding tests and support tools) is organized into the
following packages/modules:
* `orm/` package contains code that supports the general mapping of Labelbox
  data to Python objects. This includes base classes, attribute (field and
  relationship) classes, generic GraphQL queries etc.
* `schema/` package contains definitions of classes which represent data type
  (e.g. Project, Label etc.). It relies on `orm/` classes for easy and succinct
  object definitions. It also contains custom functionalities and custom GraphQL
  templates where necessary.
* `client.py` contains the `Client` class that's the client-side stub for
  communicating with Labelbox servers.
* `exceptions.py` contains declarations for all Labelbox errors.
* `pagination.py` contains support for paginated relationship and collection
  fetching.
* `utils.py` contains utility functions.

## Branches

* All development happens in per-feature branches prefixed by contributor's
  initials. For example `fs/feature_name`.
* Approved PRs are merged to the `develop` branch.
* The `develop` branch is merged to `master` on each release.

## Testing

Currently the SDK functionality is tested using integration tests. These tests
communicate with a Labelbox server (by default the staging server) and are in
that sense not self-contained. Besides that they are organized like unit test
and are based on the `pytest` library.

To execute tests you will need to provide an API key for the server you're using
for testing (staging by default) in the `LABELBOX_TEST_API_KEY` environment
variable. For more info see [Labelbox API key
docs](https://labelbox.helpdocs.io/docs/api/getting-started).

## Release Steps

Each release should follow the following steps:

1. Update the Python SDK package version in `REPO_ROOT/setup.py`
2. Make sure the `CHANGELOG.md` contains appropriate info 
3. Commit these changes and tag the commit in Git as `vX.Y`
4. Merge `develop` to `master` (fast-forward only).
5. Create a GitHub release.
6. This will kick off a Github Actions workflow that will:
  - Build the library in the [standard
  way](https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives)
  - Upload the distribution archives in the [standard
  way](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives)
  with credentials for the `labelbox` PyPI user.
  - Run the `REPO_ROOT/tools/api_reference_generator.py` script to update
  [HelpDocs documentation](https://labelbox.helpdocs.io/docs/). You will need
  to provide a HelpDocs API key for.