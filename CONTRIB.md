# Labelbox Python SDK Contribution Guide

## Contribution Guidelines
Thank you for expressing your interest in contributing to the Labelbox SDK. 
To ensure that your contribution aligns with our guidelines, please carefully 
review the following considerations before proceeding:

* For feature requests, we recommend consulting with Labelbox support or 
  creating a [Github Issue](https://github.com/Labelbox/labelbox-python/issues) on our repository.
* We can only accept general solutions that address common issues rather than solutions 
  designed for specific use cases. Acceptable contributions include simple bug fixes and 
  improvements to functions within the schema/ package.
* Please ensure that any new libraries are compliant with the Apache license that governs the Labelbox SDK.
* Ensure that you update any relevant docstrings and comments within your code
* Ensure that any new python components like classes, methods etc that need to feature in labelbox documentation have entries in the file [index.rst](https://github.com/Labelbox/labelbox-python/blob/develop/docs/source/index.rst). Also make sure you run `make html` locally in the `docs` folder to check if the documentation correctly updated according to the docstrings in the code added.

## Repository Organization

The SDK source (excluding tests and support tools) is organized into the
following packages/modules:
* `data/` package contains code that maps annotations (labels or pre-labels) to 
  Python objects, as well as serialization and deserialization tools for converting 
  between NDJson and Annotation Types.
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

## Formatting

Before making a commit, to automatically adhere to our formatting standards,
install and activate [pre-commit](https://pre-commit.com/)
```shell
pip install pre-commit
pre-commit install
```
After the above, running `git commit ...` will attempt to fix formatting,
and make necessary changes to files. You will then need to stage those files again.

You may also manually format your code by running the following:
```shell
yapf tests labelbox -i --verbose --recursive --parallel --style "google"
```


## Testing

Currently, the SDK functionality is tested using unit and integration tests. 
The integration tests communicate with a Labelbox server (by default the staging server) 
and are in that sense not self-contained.

Please consult "Testing" section in the README for more details on how to test.

Additionally, to execute tests you will need to provide an API key for the server you're using
for testing (staging by default) in the `LABELBOX_TEST_API_KEY` environment
variable. For more info see [Labelbox API key docs](https://labelbox.helpdocs.io/docs/api/getting-started).


## Release Steps

Please consult the Labelbox team for releasing your contributions

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
  
