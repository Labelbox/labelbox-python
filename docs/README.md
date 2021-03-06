# Labelbox Python SDK API Documentation

The Labelbox Python API documentation is generated from source code comments
using Sphinx (https://www.sphinx-doc.org/).

## Preparing the Sphinx environment

To generate the documentation install Sphinx and Sphinxcontrib-Napoleon. The
easiest way to do it is using a Python virtual env and pip:

```
# create a virtual environment
python3 -m venv labelbox_docs_venv

# activate the venv
source ./labelbox_docs_venv/bin/activate

# upgrade venv pip and setuptools
pip install --upgrade pip setuptools

# install Sphinx and necessary contrib from requriements
pip install -r labelbox_root/docs/requirements.txt

# install Labelbox dependencies
pip install -r labelbox_root/requirements.txt
```

There are other ways to do prepare the environment, but we highly recommend
using a Python virtual environment.

##  Generating Labelbox SDK API documentation

With the Sphinx environment prepared, enter the docs folder:

```
cd labelbox_root/docs/
```

Run the make build tool, instructing it to build docs as HTML:
```
make html
```
