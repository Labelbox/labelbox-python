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

- Use Python 3.7, 3.8 or 3.9
- [Create an account](http://app.labelbox.com/)
- [Generate an API key](https://docs.labelbox.com/docs/create-an-api-key)

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
pip install "labelbox[data]"
```

## Documentation

- [Visit our docs](https://docs.labelbox.com/reference) to learn how the SDK works
- Checkout our [notebook examples](examples/) to follow along with interactive tutorials
- view our [API reference](https://labelbox-python.readthedocs.io/en/latest/index.html).

## Authentication

Labelbox uses API keys to validate requests. You can create and manage API keys on [Labelbox](https://app.labelbox.com/account/api-keys). Pass your API key as an environment variable. Then, import and initialize the API Client.

```
user@machine:~$ export LABELBOX_API_KEY="<your local api key here>"
user@machine:~$ python3

from labelbox import Client
client = Client()
```

- Update api_key and endpoint if not using the production cloud deployment

```
# On prem
client = Client( endpoint = "<local deployment>")

# Local
client = Client(api_key=os.environ['LABELBOX_TEST_API_KEY_LOCAL'], endpoint="http://localhost:8080/graphql")

# Staging
client = Client(api_key=os.environ['LABELBOX_TEST_API_KEY_LOCAL'], endpoint="https://api.lb-stage.xyz/graphql")
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

6. Testing against Delegated Access will be skipped unless the local env contains the key:
DA_GCP_LABELBOX_API_KEY. These tests will be included when run against a PR. If you would like to test it manually, please reach out to the Devops team for information on the key.
