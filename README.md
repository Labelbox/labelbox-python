# labelbox-python

[![CircleCI](https://circleci.com/gh/Labelbox/labelbox-python.svg?style=svg)](https://circleci.com/gh/Labelbox/labelbox-python)
[![Documentation Status](https://readthedocs.org/projects/labelbox/badge/?version=latest)](https://labelbox.readthedocs.io/en/latest/?badge=latest)

Python libraries for interacting with [Labelbox](https://labelbox.com/).

## Developing

Always consult `.circleci/config.yml` to make sure your dev environment matches
up with the current testing environment.

We use Python 3.6.4 and `pipenv` to manage dependencies.

To get set up:
```sh
pipenv sync --dev
```

To run tests and the linter
```sh
pipenv run tox
```

## Releasing

```sh
pipenv run tox -e release-test
```

Check https://test.pypi.org/project/labelbox/ and if it looks good

```sh
pipenv run tox -e release
```

To generate a `requirements.txt` for usage outside of `pipenv`

```sh
pipenv lock -r > requirements.txt
```
