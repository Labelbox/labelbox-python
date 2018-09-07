# labelbox-python

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

