# Contribution Guide

Each module in this monorepo is in a folder in `libs/` with a `README.md` describing the purpose of the module and its development requirements. 

This is a general guide for all modules in this repository.

## Table of Contents

- [General Guidelines](#general-guidelines)
- [Branches](#branches-and-tags)
- [Release Steps](#release-steps)
- [Jupyter Notebooks](#jupyter-notebooks)
- [General Prerequisites](#general-prerequisites)
- [Setup and Building](#setup-and-building)
- [Testing](#testing)

## General Guidelines

Thank you for your interest in contributing! To ensure that your contribution meets our guidelines, review the following tips:

* For feature requests, ask [Labelbox Support](https://docs.labelbox.com/docs/contacting-customer-support) or create a [Github Issue](https://github.com/Labelbox/labelbox-python/issues).
* We accept general solutions that address common issues rather than specific use cases. Example contributions include a wide range of activities, such as bug fixes and updates to dependencies.
* Ensure that any new libraries comply with this repository's Apache license.
* Update any relevant docstrings and comments in the code you add or change.
* Ensure that new Python components, such as classes, packages, or methods, that need to feature in the Labelbox documentation have entries in the file [index.rst](https://github.com/Labelbox/labelbox-python/blob/develop/docs/source/index.rst).
* Add entries in [index.rst](https://github.com/Labelbox/labelbox-python/blob/develop/docs/source/index.rst) for new Python components, such as classes, packages, or methods, that need to feature in the Labelbox documentation.

## Branches and Tags

* Develop in per-feature branches prefixed by your initials. For example `fs/feature_name`.
* Approved PRs are merged to the `develop` branch.

## Release Steps

Your contributions are released when approved and merged. Consult [Labelbox Support](https://docs.labelbox.com/docs/contacting-customer-support) for a timeframe.

## General Prerequisites

Install [Rye](https://rye-up.com/) before contributing. Rye manages this repository. [See details on why we use Rye](https://alpopkes.com/posts/python/packaging_tools/). TLDR: We use Rye for Environment, Package, Python, management, and Package publishing, and building is unified under a single tool for consistency of development. Alternatively, use one of our [Docker containers](https://github.com/Labelbox/labelbox-python/pkgs/container/labelbox-python) with `Rye` set up.

**You can use Poetry to manage the virtual environment** but must manage Python yourself and must run equivalent poetry commands not listed in the documentation to perform the same general operations (testing, building, etc.). The standard `pyproject.toml` format is used. Don't check in `poetry.lock` files.

## Setup and Building

Because `Rye` is used, all modules in `libs/` must adhere to these steps:

* `rye sync` in the module folder you want to work on (EG `rye sync --all-features` to work on `labelbox`).
* `rye build` to create a distribution in `dist/` which you can install into a Python environment (EG `pip install dist/labelbox-build.tar.gz`).

To avoid virtual environment pollution, **don't** `pip install -e .` with any Labelbox module. To modify any module and make it compatible with your existing `pip` based projects, build a distribution and install it in your `pip` environment.

## Testing

Each module is expected to implement three commands for testing: unit testing, integration testing, and linting/formatting. See the details in each module's `README.md` for details.

```bash
rye run unit
rye run integration
rye run lint
```

## Documentation

To generate documentation for all modules (`ReadTheDocs`), run the following:

```bash
rye run docs
```

## Jupyter Notebooks

Samples are in the `examples` directory. Using samples for testing can increase your productivity.

Make sure your notebook uses your source code:
1. `ipython profile create`
2. `ipython locate` - shows the location of the jupyter server config file.
3. Open the ipython_config.py file (usually located in ~/.ipython/profile_default/) and add the following lines of code: 
```
c.InteractiveShellApp.exec_lines = [
  'import sys; sys.path.insert(0, "<labelbox-python root folder>")'
]
```
4. Go to the root of your project and run `jupyter notebook` to start the server.
