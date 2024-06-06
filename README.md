<p align="center" width="100%">
<img src="./docs/logo-full-black.svg"/>
</p>

[![Release Notes](https://img.shields.io/github/release/labelbox/labelbox-python)](https://github.com/Labelbox/labelbox-python/releases)
[![CI)](https://github.com/Labelbox/labelbox-python/actions/workflows/python-package-develop.yml/badge.svg?branch=develop)](https://github.com/Labelbox/labelbox-python/actions/workflows/python-package-develop.yml)
[![Downloads](https://pepy.tech/badge/labelbox)](https://pepy.tech/project/labelbox)
[![Dependency Status](https://img.shields.io/librariesio/github/labelbox/labelbox-python)](https://libraries.io/github/labelbox/labelbox-python)
[![Open Issues](https://img.shields.io/github/issues-raw/labelbox/labelbox-python)](https://github.com/labelbox/labelbox-python/issues)
[![Changelog](https://img.shields.io/badge/Changelog-Recent%20Updates-blue.svg)](https://docs.labelbox.com/changelog)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Twitter Follow](https://img.shields.io/twitter/follow/labelbox.svg?style=social&label=Follow)](https://twitter.com/labelbox)
[![LinkedIn Follow](https://img.shields.io/badge/Follow-LinkedIn-blue.svg?style=flat&logo=linkedin)](https://www.linkedin.com/company/labelbox/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/labelbox)](https://img.shields.io/pypi/pyversions/labelbox)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)

# Labelbox

Labelbox is a powerful data-centric AI platform that empowers enterprises to develop, optimize, and leverage AI to solve complex problems and drive innovation in their products and services.

With Labelbox, enterprises can easily curate and annotate data, generate high-quality human feedback data for computer vision and language models, evaluate and improve model performance, and automate tasks by seamlessly combining AI and human-centric workflows. The academic and research community also relies on Labelbox for cutting-edge AI research and experimentation.

Visit [Labelbox](http://labelbox.com/) for more information.

## Table of Contents
- [Quick Start](#quick-start)
- [Contribution Guidelines](#contribution-guidelines)
- [Develop with AI Assistance](#develop-with-ai-assistance)
- [Documentation](#documentation)
- [Jupyter Notebooks](#jupyter-notebooks)

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

**Please note that if you prefer to build and install your own version of the SDK, it is important to be aware that only tagged commits have been thoroughly tested. Building from the head of develop branch carries some level of risk.**

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

You should be set! Running the snippet above should create a dataset called `Test Dataset` with its content being `My First Data Row`. You can log into [Labelbox](http://labelbox.com/) to verify this. If you have any issues please file a Github Issue or contact [Labelbox Support](https://docs.labelbox.com/docs/contacting-customer-support) directly. For more advanced examples and information on the SDK, see [Documentation](#documentation) below.

## Contribution Guidelines
We encourage anyone to contribute to this repository to help improve it. Please refer to [Contributing Guide](CONTRIBUTING.md) for detailed information on how to contribute. This guide also includes instructions for how to build and run the SDK locally.

## Develop with AI assistance
### Use the codebase as context for large language models
Using the [GPT repository loader](https://github.com/mpoon/gpt-repository-loader), we have created `lbx_prompt.txt` that contains data from all `.py` and `.md` files. The file has about 730k tokens. We recommend using Gemini 1.5 Pro with 1 million context length window.

## Documentation
The SDK is well-documented to help developers get started quickly and use the SDK effectively. Here are links to that documentation:

- [Labelbox Official Documentation](https://docs.labelbox.com/docs/overview)
- [Jupyter Notebook Examples](https://github.com/Labelbox/labelbox-python/tree/develop/examples)
- [Python SDK Reference](https://labelbox-python.readthedocs.io/en/latest/)

## Jupyter Notebooks
We have samples in the `examples` directory to help you get started with the SDK.

Make sure your notebook will use your source code:
1. `ipython profile create`
2. `ipython locate` - will show where the config file is. This is the config file used by the Jupyter server, since it runs via ipython
3. Open the file (this should be ipython_config.py and it is usually located in ~/.ipython/profile_default) and add the following line of code: 
```
c.InteractiveShellApp.exec_lines = [
  'import sys; sys.path.insert(0, "<labelbox-python root folder>")'
]
```
4. Go to the root of your project and run `jupyter notebook` to start the server.

## Provenance

To enhance the software supply chain security of Labelbox's users, as of v3.73.0, every SDK release contains a [SLSA Level 3 Provenance](https://github.com/slsa-framework/slsa-github-generator/blob/main/internal/builders/generic/README.md) document.  
The provenance document refers to the Python wheel, as well as the generated docker image.  
You can use [SLSA framework's official verifier](https://github.com/slsa-framework/slsa-verifier) to verify the provenance.  
Example of usage for the v3.73.0 release wheel:

```
pip download --no-deps labelbox==3.72.0

slsa-verifier verify-artifact --source-branch develop --builder-id 'https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v2.0.0' --source-uri "git+https://github.com/Labelbox/labelbox-python-slsa-temp" --provenance-path multiple.intoto.jsonl ./labelbox-3.72.0-py3-none-any.whl
```

Example of usage for the v3.73.0 release docker image:
```
Brew install crane
brew install slsa-verifier
IMAGE=ghcr.io/labelbox/labelbox-python-slsa-temp:6.5
IMAGE="${IMAGE}@"$(crane digest "${IMAGE}")
slsa-verifier verify-image "$IMAGE" \
    --source-uri github.com/Labelbox/labelbox-python-slsa-temp
```
