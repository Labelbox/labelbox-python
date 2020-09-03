# Labelbox Python SDK

Labelbox is the enterprise-grade training data solution with fast AI enabled labeling tools, labeling automation, human workforce, data management, a powerful API for integration & SDK for extensibility. Visit http://labelbox.com/ for more information.

The Labelbox Python API offers a simple, user-friendly way to interact with the Labelbox back-end.

## Requirements

* Use Python 3.6 or 3.7.
* Create an account by visiting http://app.labelbox.com/.
* [Generate an API key](https://labelbox.com/docs/api/api-keys).

## Installation & authentication

1. Install using Python's Pip manager.
```
pip install labelbox
```

2. Pass your API key as an environment variable. Then, import and initialize the API Client.
```
user@machine:~$ export LABELBOX_API_KEY="<your api key here>"
user@machine:~$ python3

from labelbox import Client
client = Client()
```

## Documentation

[Visit our docs](https://labelbox.com/docs/python-api) to learn how to [create a project](https://labelbox.com/docs/python-api/create-first-project), read through some helpful user guides, and view our [API reference](https://labelbox.com/docs/python-api/api-reference).

## Repo Organization and Contribution
Please consult `CONTRIB.md`

## Testing
1. Update the `Makefile` with your `staging` or `prod` API key.  Make sure the key is not from a free tier account.
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
