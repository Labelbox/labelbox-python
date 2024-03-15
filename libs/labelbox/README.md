# Labelbox

Core mono-module for Labelbox's SDK. For full detailed information,
please go to Labelbox's [Github Page](https://github.com/Labelbox/labelbox-python).

## Repository Organization

The SDK source (excluding tests and support tools) is organized into the
following packages/modules:
* `data/` package contains code that maps annotations (labels or pre-labels) to 
  Python objects, as well as serialization and deserialization tools for converting 
  between NDJson and Annotation Types.
* `orm/` package contains code that supports the general mapping of Labelbox
  data to Python objects. This includes base classes, attribute (field and
  relationship) classes, generic GraphQL queries etc.
* `schema/` package contains definitions of classes which represent data type
  (e.g. Project, Label etc.). It relies on `orm/` classes for easy and succinct
  object definitions. It also contains custom functionalities and custom GraphQL
  templates where necessary.
* `client.py` contains the `Client` class that's the client-side stub for
  communicating with Labelbox servers.
* `exceptions.py` contains declarations for all Labelbox errors.
* `pagination.py` contains support for paginated relationship and collection
  fetching.
* `utils.py` contains utility functions.
