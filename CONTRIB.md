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

## Commits

Before making a commit, to automatically adhere to our formatting standards,
install and activate [pre-commit](https://pre-commit.com/)

After the above, running `git commit ...` will attempt to fix formatting. If
there was formatted needed, you will need to re-add and re-commit before pushing.

## Testing

Currently, the SDK functionality is tested using integration tests. These tests
communicate with a Labelbox server (by default the staging server) and are in
that sense not self-contained. Besides, that they are organized like unit test
and are based on the `pytest` library.

To execute tests you will need to provide an API key for the server you're using
for testing (staging by default) in the `LABELBOX_TEST_API_KEY` environment
variable. For more info see [Labelbox API key docs](https://labelbox.helpdocs.io/docs/api/getting-started).

To pass tests, code must be formatted. If pre-commit was not installed, 
you will need to use the following command:

```shell
yapf tests labelbox -i --verbose --recursive --parallel --style "google"
```

## Release Steps

Each release should follow the following steps:

1. Update the Python SDK package version in `REPO_ROOT/setup.py`
2. Make sure the `CHANGELOG.md` contains appropriate info
3. Commit these changes and tag the commit in Git as `vX.Y`
4. Merge `develop` to `master` (fast-forward only).
5. Create a GitHub release.
6. This will kick off a Github Actions workflow that will:
  - Build the library in the [standard way](https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives)
  - Upload the distribution archives in the [standard way](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives)
 - with credentials for the `labelbox` PyPI user.
  
  ## Running Jupyter Notebooks
  
  We have plenty of good samples in the _examples_ directory and using them for testing can help us increase our productivity. One way to use jupyter notebooks is to run the jupyter server locally (another way is to use a VSC plugin, not documented here). It works really fast.
  
  Make sure your notebook will use your source code:
  1. `ipython profile create`
  2. `ipython locate` - will show where the config file is. This is the config file used by the jupyter server, since it runs via ipython
  3. Open the file (this should be ipython_config.py and it is usually located in ~/.ipython/profile_default) and add the following line of code: 
  ```
  c.InteractiveShellApp.exec_lines = [
    'import sys; sys.path.insert(0, "<labelbox-python root folder>")'
  ]
  ```
  4. Go to the root of your project and run `jupyter notebook` to start the server
  
