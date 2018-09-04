from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    long_description = f.read()


requirements = [
        'jinja2',
        'pillow',
        'requests',
        'shapely',
        ]

dev_requirements = [
        'pytest',
        'xmltodict',
        ]

setup(
    name='LBExporters',
    version='0.1.1',
    packages=['labelbox2coco', 'labelbox2pascal'],
    licence='Apache 2.0',
    description='Converters from Labelbox exports to other common foramts',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
    },
)
