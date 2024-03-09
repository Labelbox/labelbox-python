# Labelbox Python SDK
[![Release Notes](https://img.shields.io/github/release/labelbox/labelbox-python)](https://github.com/Labelbox/labelbox-python/releases)
[![CI](https://github.com/labelbox/labelbox-python/actions/workflows/python-package.yml/badge.svg)](https://github.com/labelbox/labelbox-python/actions)
[![Downloads](https://pepy.tech/badge/labelbox)](https://pepy.tech/project/labelbox)
[![Dependency Status](https://img.shields.io/librariesio/github/labelbox/labelbox-python)](https://libraries.io/github/labelbox/labelbox-python)
[![Open Issues](https://img.shields.io/github/issues-raw/labelbox/labelbox-python)](https://github.com/labelbox/labelbox-python/issues)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Twitter Follow](https://img.shields.io/twitter/follow/labelbox.svg?style=social&label=Follow)](https://twitter.com/labelbox)
[![LinkedIn Follow](https://img.shields.io/badge/Follow-LinkedIn-blue.svg?style=flat&logo=linkedin)](https://www.linkedin.com/company/labelbox/)


Labelbox is a cloud-based data-centric AI platform designed to help teams create high-quality training data for their AI models. It provides a suite of tools and features that streamline the process of data curation, labeling, model output evaluation for computer vision and large language models. Visit [Labelbox](http://labelbox.com/) for more information.


The Python SDK provides a convenient way to interact with Labelbox programmatically, offering advantages over REST or GraphQL APIs:

* **Simplified interactions:** The SDK abstracts away the complexities of API calls, making it easier to work with Labelbox.
* **Object-oriented approach:** The SDK provides an object-oriented interface, allowing you to interact with Labelbox entities (projects, datasets, labels, etc.) as Python objects.
* **Extensibility:** The SDK can be extended to support custom data formats and operations.

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

## Installation
![Python Version](https://img.shields.io/badge/python-3.7%20|%203.8%20|%203.9%20|%203.10-blue.svg)

Welcome to the quick start guide for integrating Labelbox into your Python projects. Whether you're looking to incorporate advanced data labeling into your workflow or simply explore the capabilities of the Labelbox Python SDK, this guide will walk you through the two main methods of setting up Labelbox in your environment: via a package manager and by building it locally.

### Easy Installation with Package Manager

To get started with the least amount of hassle, follow these simple steps to install the Labelbox Python SDK using pip, Python's package manager.

1. **Ensure pip is Installed:** First, make sure you have `pip` installed on your system. It's the tool we'll use to install the SDK.
   
2. **Sign Up for Labelbox:** If you haven't already, create a free account at [Labelbox](http://app.labelbox.com/) to access its features.

3. **Generate Your API Key:** Log into Labelbox and navigate to [Account > API Keys](https://docs.labelbox.com/docs/create-an-api-key) to generate an API key. You'll need this for programmatic access to Labelbox.

4. **Install the SDK:** Open your terminal or command prompt and run the following command to install the Labelbox Python SDK:
   
   ```bash
   pip install labelbox
   ```

5. **Install Optional Dependencies:** For enhanced functionality, such as data processing, you can install additional dependencies with:
   
   ```bash
   pip install "labelbox[data]"
   ```

   This includes essential libraries like Shapely, GeoJSON, NumPy, Pillow, and OpenCV-Python, enabling you to handle a wide range of data types and perform complex operations.

### Building and Installing Locally

For those who prefer or require a more hands-on approach, such as contributing to the SDK or integrating it into a complex project, building the SDK locally is the way to go.

#### Prerequisites

- **pip Installation:** Ensure `pip` is installed on your system. For macOS users, you can easily set it up with:
  
  ```bash
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python3 get-pip.py
  ```

  If you encounter a warning about `pip` not being in your PATH, you'll need to add it manually by modifying your shell configuration (`.zshrc`, `.bashrc`, etc.):

  ```bash
  export PATH=/Users/<your-macOS-username>/Library/Python/3.8/bin:$PATH
  ```

#### Steps for Local Installation

1. **Clone the SDK Repository:** First, clone the Labelbox SDK repository from GitHub to your local machine.

2. **Install the SDK Locally:** Navigate to the root directory of the cloned repository and run:

   ```bash
   pip3 install -e .
   ```

3. **Install Required Dependencies:** To ensure all dependencies are met, run:

   ```bash
   pip3 install -r requirements.txt
   ```

   For additional data processing capabilities, remember to install the `data` extra as mentioned in the easy installation section.


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
