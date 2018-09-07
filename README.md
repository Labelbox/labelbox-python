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
pipenv run python setup.py sdist bdist_wheel
twine upload --repository-url 'https://test.pypi.org/legacy/' 'dist/*'
```

If it looks good
```sh
twine upload 'dist/*'
```
