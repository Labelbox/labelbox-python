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


### Table of Contents
- [Installation](#installation)
    - [Easy Installation with Package Manager](#easy-installation-with-package-manager)
    - [Building and Installing Locally](#building-and-installing-locally)
        - [Prerequisites](#prerequisites)
        - [Steps for Local Installation](#steps-for-local-installation)
- [Code Architecture](#code-architecture)
- [Extending the SDK](#extending-the-sdk)
    - [Adding an Export Format Converter](#adding-an-export-format-converter)
- [Contribution Guidelines](#contribution-guidelines)
- [Develop with AI Assistance](#develop-with-ai-assistance)
- [Documentation](#documentation)
    - [Official Documentation](#official-documentation)
    - [Notebook Examples](#notebook-examples)
    - [API Reference](#api-reference)


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


## Code Architecture
The Labelbox Python SDK is designed to provide a clean and intuitive interface for interacting with the Labelbox API. It primarily uses GraphQL for communication, with some REST API calls for specific functionalities. The SDK wraps the GraphQL API calls and provides object-oriented representations of Labelbox entities like projects, datasets, and labels. This allows developers to interact with Labelbox in a more Pythonic way, making code easier to read and maintain.

Key files and classes include:

- **`labelbox/client.py`:** Contains the `Client` class, which provides methods for interacting with the Labelbox API.
- **`labelbox/orm/model.py`:** Defines the data model for Labelbox entities like projects, datasets, and labels.
- **`labelbox/schema/*.py`:** Contains classes representing specific Labelbox entities and their attributes.
- **`labelbox/data/annotation_types/*.py`:** Defines classes for different annotation types, such as bounding boxes, polygons, and classifications.
- **`labelbox/data/serialization/*.py`:** Provides converters for different data formats, including NDJSON and Labelbox v1 JSON.

The SDK wraps the GraphQL APIs and provides a Pythonic interface for interacting with Labelbox.

## Contribution guidelines
We encourage developers to contribute to the Labelbox Python SDK and help improve its functionality and usability. Please refer to the `CONTRIB.md` file in the root folder of the repository for detailed information on how to contribute.

## Develop with AI assistance
### Load this repo code as context for large language models
Using the [GPT repository loader](https://github.com/mpoon/gpt-repository-loader), we have created `lbx_prompt.txt` that contains data from all `.py` and `.md` files. The file has about 730k tokens. We recommend using Gemini 1.5 Pro with 1 million context length window

### Ask Google Gemini to get started
#### Adding a method to convert export v2 to COCO format in Labelbox Python SDK

To add a method to the Labelbox Python SDK that converts export v2 into COCO format, you can follow these steps:

**1. Create a new Python file:**

Create a new file named `coco_converter.py` inside the `labelbox/schema/` directory. This file will contain the logic for converting export v2 data to COCO format.

**2. Implement the conversion logic:**

Inside `coco_converter.py`, define a function named `export_v2_to_coco`. This function should accept the export v2 data as input and perform the necessary conversion steps to generate the COCO format data structures. You can utilize existing libraries like `pycocotools` to achieve this.

Here's a basic example of how the function might look:

```python
from labelbox.schema.export_task import ExportTask
from pycocotools.coco import COCO

def export_v2_to_coco(export_task: ExportTask) -> COCO:
    # Extract data from export_task
    # ...
    
    # Convert data to COCO format using pycocotools
    # ...
    
    # Return COCO object
    return coco_object
```

**3. Add the method to the utilities module:**

Open the `labelbox/utilities.py` file and import the newly created `export_v2_to_coco` function. Then, add the function as a method to the `Utilities` class:

```python
from labelbox.schema.coco_converter import export_v2_to_coco

class Utilities:
    # ... existing methods ...

    def export_v2_to_coco(self, export_task: ExportTask) -> COCO:
        return export_v2_to_coco(export_task)
```

**4. Update the documentation:**

Modify the README.md file to include information about the new `export_v2_to_coco` method in the `client.utilities` section. This will help users understand how to use the new functionality.

**5. Test the implementation:**

Write unit tests for the `export_v2_to_coco` function to ensure it works as expected with different export v2 data structures. This will help maintain the quality and reliability of the SDK.

By following these steps, you can successfully add a method to the Labelbox Python SDK that converts export v2 data to COCO format, making it readily available for users through `client.utilities.export_v2_to_coco()`.

## Documentation
The Labelbox Python SDK is well-documented to help developers get started quickly and use the SDK effectively. Here are some resources:

- **Official Documentation:** https://docs.labelbox.com/docs/overview
- **Notebook Examples:** https://github.com/Labelbox/labelbox-python/tree/master/examples
- **API Reference:** https://labelbox-python.readthedocs.io/en/latest/
