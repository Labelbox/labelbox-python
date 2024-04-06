# Labelbox

Core mono-module for Labelbox's Python SDK.

## Table of Contents

- [Setup](#setup)
- [Repository Organization](#repository-organization)
- [Testing](#testing)

## Setup

```bash
rye sync --all-features # to install labelbox[data] dependencies
```

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

## Testing

### Unit Testing

```bash
rye run unit
```

### Integration Testing

```bash
LABELBOX_TEST_API_KEY="YOUR_API_TEST_KEY" LABELBOX_TEST_ENVIRON="prod" rye run integration
```
For more info on how to get a `LABELBOX_TEST_API_KEY` [Labelbox API key docs](https://labelbox.helpdocs.io/docs/api/getting-started). 

**Integration tests by default will run against your account that you provide an API Key from and modify its data. If you want to run integration tests, without it impacting your existing account, create an additional account using a secondary e-mail on [Labelbox](https://labelbox.com). Free accounts are sufficent for integration testing purposes.**

You can also use a `.env` file if you prefer instead of needing to type out the environmental overrides every single time you want to run commands. Please add a `--env-file` parameter to the test command (EG `rye --env-file=.env run integration`).

### (Optional) Data Testing

For testing the impact of the extra installs included with `labelbox[data]`, run the following:

```bash
LABELBOX_TEST_API_KEY="YOUR_API_TEST_KEY" LABELBOX_TEST_ENVIRON="prod" rye run data
```

By default `rye sync` does not install the extra packages needed in `labelbox[data]`. You'll need to run `rye sync --all-features`. Do not checkin `requirements.lock` or `requirements-dev.lock` after doing this.

### Linting / Formatting

Before making a commit, to automatically adhere to our formatting standards, it is recommended to install and activate [pre-commit](https://pre-commit.com/)
```shell
pip install pre-commit
pre-commit install
```
After the above, running `git commit ...` will attempt to fix formatting,
and make necessary changes to files. You will then need to stage those files again.

You may also manually format your code by running the following:
```bash
rye run lint
```

### Documentation

To generate documentation for all modules (`ReadTheDocs`), run the following command.

```bash
rye run docs
```