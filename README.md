# Labelbox Python SDK

Labelbox is the enterprise-grade training data solution with fast AI enabled labeling tools, labeling automation, human workforce, data management, a powerful API for integration & SDK for extensibility. Visit [Labelbox](http://labelbox.com/) for more information.

The Labelbox Python API offers a simple, user-friendly way to interact with the Labelbox back-end.

## Table of Contents

- [Labelbox Python SDK](#labelbox-python-sdk)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [Note for Windows users](#note-for-windows-users)
  - [Documentation](#documentation)
  - [Authentication](#authentication)
  - [Contribution](#contribution)
  - [Testing](#testing)

## Requirements

* Use Python 3.6, 3.7 or 3.8
* [Create an account](http://app.labelbox.com/)
* [Generate an API key](https://labelbox.com/docs/api/getting-started#create_api_key)

## Installation

Prerequisite: Install pip

`pip` is a package manager for Python. **On macOS**, you can set it up to use the default python3 install via -
```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

If the installation completes with a warning re: pip not being in your path, you'll need to add it by modifying your shell config (`.zshrc`, `.bashrc` or similar). You might have to modify the command below depending on the version of python3 on your machine.

```
export PATH=/Users/<your-macOS-username>/Library/Python/3.8/bin:$PATH
```

Install SDK locally, using Python's Pip manager
```
pip3 install -e .
```

Install dependencies
```
pip3 install -r requirements.txt
```
To install dependencies required for data processing modules use:
```
pip install labelbox[data]
```
### Note for Windows users
The package `rasterio` installed by `labelbox[data]` relies on GDAL which could be difficult to install on Microsoft Windows.

You may see the following error message:

```
INFO:root:Building on Windows requires extra options to setup.py to locate needed GDAL files. More information is available in the README.

ERROR: A GDAL API version must be specified. Provide a path to gdal-config using a GDAL_CONFIG environment variable or use a GDAL_VERSION environment variable.
```

As a workaround:

1. Download the binary files for GDAL and rasterio:

    a. From https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal, download `GDAL‑3.3.2‑cp38‑cp38‑win_amd64.wh`

    b. From https://www.lfd.uci.edu/~gohlke/pythonlibs/#rasterio, download `rasterio‑1.2.9‑cp38‑cp38‑win_amd64.whl`

    Note: You need to download the right files for your Python version. In the files above `cp38` means CPython 3.8.

2. After downloading the files, please run the following commands, in this particular order.

```
pip install GDAL‑3.3.2‑cp38‑cp38‑win_amd64.wh
pip install rasterio‑1.2.9‑cp38‑cp38‑win_amd64.whl
pip install labelbox[data]
```

This should resolve the error message.


## Documentation

* [Visit our docs](https://labelbox.com/docs/python-api) to learn how the SDK works
* Checkout our [notebook examples](examples/) to follow along with interactive tutorials
* view our [API reference](https://labelbox.com/docs/python-api/api-reference).

## Authentication

Labelbox uses API keys to validate requests. You can create and manage API keys on [Labelbox](https://app.labelbox.com/account/api-keys). Pass your API key as an environment variable. Then, import and initialize the API Client.

```
user@machine:~$ export LABELBOX_API_KEY="<your local api key here>"
user@machine:~$ python3

from labelbox import Client
client = Client()
```
* Update api_key and endpoint if not using the production cloud deployment
```
# On prem
client = Client( endpoint = "<local deployment>")

# Local
client = Client(api_key=os.environ['LABELBOX_TEST_API_KEY_LOCAL'], endpoint="http://localhost:8080/graphql")

# Staging
client = Client(api_key=os.environ['LABELBOX_TEST_API_KEY_LOCAL'], endpoint="https://staging-api.labelbox.com/graphql")
```

## Contribution
Please consult `CONTRIB.md`

## Testing
1. Update the `Makefile` with your `local`, `staging`, `prod` API key. Ensure that docker has been installed on your system. Make sure the key is not from a free tier account.
2. To test on `local`:
```
user@machine:~$ export LABELBOX_TEST_API_KEY_LOCAL="<your local api key here>"
make test-local  # with an optional flag: PATH_TO_TEST=tests/integration/...etc LABELBOX_TEST_API_KEY_LOCAL=specify_here_or_export_me
```

3. To test on `staging`:
```
user@machine:~$ export LABELBOX_TEST_API_KEY_STAGING="<your staging api key here>"
make test-staging # with an optional flag: PATH_TO_TEST=tests/integration/...etc LABELBOX_TEST_API_KEY_STAGING=specify_here_or_export_me
```

4. To test on `prod`:
```
user@machine:~$ export LABELBOX_TEST_API_KEY_PROD="<your prod api key here>"
make test-prod # with an optional flag: PATH_TO_TEST=tests/integration/...etc LABELBOX_TEST_API_KEY_PROD=specify_here_or_export_me
```

5. If you make any changes and need to rebuild the image used for testing, force a rebuild with the `-B` flag
```
make -B {build|test-staging|test-prod}
```
