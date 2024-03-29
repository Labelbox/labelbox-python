# Labelbox Python SDK
[![Release Notes](https://img.shields.io/github/release/labelbox/labelbox-python)](https://github.com/Labelbox/labelbox-python/releases)
[![CI](https://github.com/Labelbox/labelbox-python/actions/workflows/python-package-develop.yaml/badge.svg)](https://github.com/Labelbox/labelbox-python/actions/workflows/python-package-develop.yaml)
[![Downloads](https://pepy.tech/badge/labelbox)](https://pepy.tech/project/labelbox)
[![Dependency Status](https://img.shields.io/librariesio/github/labelbox/labelbox-python)](https://libraries.io/github/labelbox/labelbox-python)
[![Open Issues](https://img.shields.io/github/issues-raw/labelbox/labelbox-python)](https://github.com/labelbox/labelbox-python/issues)
[![Changelog](https://img.shields.io/badge/Changelog-Recent%20Updates-blue.svg)](https://docs.labelbox.com/changelog)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Twitter Follow](https://img.shields.io/twitter/follow/labelbox.svg?style=social&label=Follow)](https://twitter.com/labelbox)
[![LinkedIn Follow](https://img.shields.io/badge/Follow-LinkedIn-blue.svg?style=flat&logo=linkedin)](https://www.linkedin.com/company/labelbox/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/labelbox)](https://img.shields.io/pypi/pyversions/labelbox)

Labelbox is focused on building a data-centric AI platform for enterprises to develop, optimize, and use AI to solve problems and power new products and services.

Enterprises use Labelbox to curate data, generate high-quality human feedback data for computer vision and LLMs, evaluate model performance, and automate tasks by combining AI and human-centric workflows. The academic & research community uses Labelbox for cutting-edge AI research.

Visit [Labelbox](http://labelbox.com/) for more information.

## Table of Contents
- [Quick Start](#quick-start)
- [Contribution Guidelines](#contribution-guidelines)
- [Develop with AI Assistance](#develop-with-ai-assistance)
- [Documentation](#documentation)

## Quick Start
   
### Sign Up
If you haven't already, create a free account at [Labelbox](http://app.labelbox.com/).

### Generate an API key
Log into Labelbox and navigate to [Account > API Keys](https://docs.labelbox.com/docs/create-an-api-key) to generate an API key. 

### Install

To install the SDK, run the following command.

```bash
pip install labelbox
```

If you'd like to install the SDK with enhanced functionality, which additional optional capabilities surrounding data processing, run the following command.

```bash
pip install "labelbox[data]"
```

**If you want to installed a version of Labelbox built locally, be aware that only tagged commits have been validated to fully work! Installing the latest from develop is at your own risk!**

### Validate Installation and API Key

After installing the SDK and getting an API Key, it's time to validate them both. 

```python
import labelbox as lb

client = lb.Client(API_KEY) # API_KEY = API Key generated from labelbox.com
dataset = client.create_dataset(name="Test Dataset")
data_rows = [{"row_data": "My First Data Row", "global_key": "first-data-row"}]
task = dataset.create_data_rows(data_rows)
task.wait_till_done()
```

You should be set! Running the snippet above should create a dataset called `Test Dataset` with a single datarow with the text contents being `My First Data Row`. You can log into [Labelbox](http://labelbox.com/) to verify this. If you have any issues please file a Github Issue or contact [Labelbox Support](https://docs.labelbox.com/docs/contacting-customer-support)  directly. For more advanced examples and information on the SDK, see [Documentation](#documentation) below.

## Contribution Guidelines
We encourage anyone to contribute to this repository to help improve it. Please refer to [Contributing Guide](CONTRIBUTING.md) for detailed information on how to contribute. This guide also includes instructions for how to build and run the SDK locally.

## Develop with AI assistance
### Use the codebase as context for large language models
Using the [GPT repository loader](https://github.com/mpoon/gpt-repository-loader), we have created `lbx_prompt.txt` that contains data from all `.py` and `.md` files. The file has about 730k tokens. We recommend using Gemini 1.5 Pro with 1 million context length window.

## Documentation
The SDK is well-documented to help developers get started quickly and use the SDK effectively. Here are some resources:

- [Labelbox Official Documentation](https://docs.labelbox.com/docs/overview)
- [Jupyter Notebook Examples](https://github.com/Labelbox/labelbox-python/tree/master/examples)
- [Python SDK reference docs](https://labelbox-python.readthedocs.io/en/latest/)
