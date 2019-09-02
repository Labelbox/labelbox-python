# Labelbox Python API

Labelbox is the training data workbench for ML teams. It allows you to label
data with the fastest and most intuitive annotation tools. Visit
https://labelbox.com/ for more information.

The Labelbox Python API allows you to interact with Labelbox back-end in a
simple, user-friendly way.

## Requirements

To use the Labelbox Python API you will need a Labelbox account. Once you login
to the Labelbox web page, generate an API key as described in the documentation:
https://labelbox.com/docs/api/api-keys. Store the key to a safe location. You
will need it for using the Labelbox Python API.

## Installation

Labelbox Python API can be installed using Python's Pip manager:
```
pip install labelbox
```

## Usage

### API Key

Your Labelbox API key is required to execute the library. It can be passed to
Labelbox Python API via an environment variable `LABELBOX_API_KEY`. It is then
automatically picked up by the `Client`:
```
from labelbox import Client
client = Client() # will use the API key from the environment variable
```

Alternatively you can pass it to the `Client` object initialization:
```
from labelbox import Client
client = Client("<your_api_key_here>")
```

### Basic commands

The Labelbox Python API allows you to create, update and delete all standard
Labelbox data types, such as Projects, Datasets, DataRows, Labels and others.
For more info about the Labelbox data model please visit
https://labelbox.com/docs.

Here is an example code for uploading some data from scratch:
```
from labelbox import Client

client = Client()

# Create a project and a dataset , automatically reflected on the server
project = client.create_project(name="My Great Project")
dataset = client.create_dataset(name="My Dataset")
project.datasets.connect(dataset)

# Upload some files to the dataset
task = dataset.create_data_rows(['file1.jpg', 'file2.jpg'])
# Bulk DataRow creation might take a while on the server-side
task.wait_till_done()

# Your data is now uploaded to Labelbox and ready for labeling!
```
