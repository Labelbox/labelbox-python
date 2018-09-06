# labelbox-python

Python libraries for interacting with [Labelbox](https://labelbox.com/).

## Releasing

```sh
pipenv run python setup.py sdist bdist_wheel
twine upload --repository-url 'https://test.pypi.org/legacy/' 'dist/*'
```

If it looks good
```sh
twine upload 'dist/*'
```
