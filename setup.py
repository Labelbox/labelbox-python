from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    long_description = f.read()


requirements = [
        'jinja2',
        'pillow',
        'rasterio',
        'requests',
        'shapely',
        'simplification',
        ]

dev_requirements = [
        'numpy',
        'pylint',
        'pytest',
        'pytest-cov',
        'tox',
        'xmltodict',
        ]

setup(
    name='labelbox',
    version='0.0.1.dev0',
    packages=[
        'labelbox.exporters',
        'labelbox.exporters.pascal_voc_writer',
        'labelbox.predictions',
    ],
    license='Apache 2.0',
    author='Feynman Liang',
    author_email='feynman@labelbox.com',
    url='https://github.com/Labelbox/labelbox-python',
    description='A python library for interacting with labelbox.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
    },
    include_package_data=True,
)
