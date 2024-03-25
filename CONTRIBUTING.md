# Labelbox Python SDK Contribution Guide

## Table of Contents
- [Contribution Guidelines](#contribution-guidelines)
- [Branches](#branches)
- [Release Steps](#release-steps)
- [Jupyter Notebooks](#jupyter-notebooks)
- [Contribution Prerequisites](#contribution-prerequisites)
- [Building Locally](#building-locally)
- [Testing](#testing)

## Contribution Guidelines
Thank you for expressing your interest in contributing to the SDK. To ensure that your contribution aligns with our guidelines, please carefully review the following before proceeding:

* For feature requests, we recommend consulting with [Labelbox Support](https://docs.labelbox.com/docs/contacting-customer-support) support or creating a [Github Issue](https://github.com/Labelbox/labelbox-python/issues).
* We can only accept general solutions that address common issues rather than solutions designed for specific use cases. Example contributions include bug fixes and dependency upgrades.
* Please ensure that any new libraries are compliant with the Apache license that governs the SDK.
* Ensure that you update any relevant docstrings and comments within your code.
* Ensure that any new Python components, such as classes, packages, or methods, that need to feature in the Labelbox documentation have entries in the file [index.rst](https://github.com/Labelbox/labelbox-python/blob/develop/docs/source/index.rst). Also, make sure you run `make html` locally in the `docs` folder to check if the documentation is correctly updated according to the docstrings in the code added.

## Branches
* All development happens in per-feature branches prefixed by contributor's initials. For example `fs/feature_name`.
* Approved PRs are merged to the `develop` branch.
* The `develop` branch is merged to `master` on each release.

## Release Steps
Please consult the [Labelbox](https://docs.labelbox.com/docs/contacting-customer-support) team for releasing your contributions.

## Contribution Prerequisites

The SDK repository is laid out as a monorepo in `libs/`. Each module under `libs/` should describe the purpose of the module and specific development requirements. 

The tool that is being used to manage the monorepo is [Rye](https://rye-up.com/) which means you need to install it before contributing or building any of them locally. 

To understand why Rye was chosen, see [here](https://alpopkes.com/posts/python/packaging_tools/). TLDR: Environment, Package, Python, management along with Package publishing and Package building is unified under a single tool for consistency of environment for SDK development.

If you want to not deal with setting up `Rye` on your local machine directly, feel free to use one of [Docker containers](https://github.com/Labelbox/labelbox-python/pkgs/container/labelbox-python) we have built which contains the entire SDK with `Rye` setup for you already.

**You can use Poetry to manage the virtual environment.** There's nothing blocking you from using Poetry to manage the virtual environment as the standard `pyproject.toml` format is used, but you'll have to deal with managing Python yourself + be asked not to check in any `poetry.lock` files. Also, you'll have to run equivalent poetry commands that may not be listed in the documentation to perform the same general operations (testing, building, etc.).

## Building Locally

These are general steps that all modules in `libs/` adhere to give the prerequisite of the installation of `Rye`.

1. Run `rye sync` in the module folder you want to work on (EG `rye sync --all-features` to work on `labelbox`).
2. Run `rye build` to create a distribution in `dist/` which you can install into a Python environment (EG `pip install dist/labelbox-build.tar.gz`).

It is generally **not** recommended to do `pip install -e .` with any Labelbox module to avoid virtual environment pollution. If you really want to modify the SDK while making it compatible with your existing `pip` based projects, use the method listed above.

## Testing

Each module within the repository will generally have three components to testing: unit testing, integration testing, and linting/formatting.

### Unit Testing

```bash
rye run unit
```

### Integration Testing

```bash
LABELBOX_TEST_API_KEY="YOUR_API_TEST_KEY" rye run integration
```
For more info on how to get a `LABELBOX_TEST_API_KEY` [Labelbox API key docs](https://labelbox.helpdocs.io/docs/api/getting-started). 

**Integration tests by default will run against your account that you provide an API Key from and modify its data. If you want to run integration tests, without it impacting your existing account, create an additional account using a secondary e-mail on [Labelbox](https://labelbox.com). Free accounts are sufficent for integration testing purposes.**

### (Optional) Data Testing

For testing the impact of the extra installs included with `labelbox[data]`, run the following:

```bash
LABELBOX_TEST_API_KEY="YOUR_API_TEST_KEY" rye run data
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

To generate `ReadTheDocs,` run the following command.

```bash
rye run docs
```

## Jupyter Notebooks

We have samples in the `examples` directory and using them for testing can help increase your productivity.

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
  









