# Labelbox Python SDK

Labelbox is the enterprise-grade training data solution with fast AI enabled labeling tools, labeling automation, human workforce, data management, a powerful API for integration & SDK for extensibility. Visit [Labelbox](http://labelbox.com/) for more information.

The Labelbox Python API offers a simple, user-friendly way to interact with the Labelbox back-end.

## Table of Contents

* [Requirements](#requirements)
* [Installation](#installation)
* [Documentation](#documentation)
* [Authentication](#authentication)
* [Contribution](#contribution)
* [Testing](#testing)

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

Install using Python's Pip manager.
```
pip install labelbox
```

## Documentation

* [Visit our docs](https://labelbox.com/docs/python-api) to learn how the SDK works
* Checkout our [notebook examples](examples/) to follow along with interactive tutorials
* view our [API reference](https://labelbox.com/docs/python-api/api-reference).

## Authentication

Labelbox uses API keys to validate requests. You can create and manage API keys on [Labelbox](https://app.labelbox.com/account/api-keys). Pass your API key as an environment variable. Then, import and initialize the API Client.

```
user@machine:~$ export LABELBOX_API_KEY="<your api key here>"
user@machine:~$ python3

from labelbox import Client
client = Client()
```

## Contribution
Please consult `CONTRIB.md`

## Testing
1. Update the `Makefile` with your `staging` or `prod` API key. Ensure that docker has been installed on your system. Make sure the key is not from a free tier account.
2. To test on `staging`:
```
make test-staging
```

3. To test on `prod`:
```
make test-prod
```

4. If you make any changes and need to rebuild the image used for testing, force a rebuild with the `-B` flag
```
make -B {build|test-staging|test_prod}
```
