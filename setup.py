import setuptools

with open('labelbox/__init__.py') as fid:
    for line in fid:
        if line.startswith('__version__'):
            SDK_VERSION = line.strip().split()[-1][1:-1]
            break

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="labelbox",
    version=SDK_VERSION,
    author="Labelbox",
    author_email="engineering@labelbox.com",
    description="Labelbox Python API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://labelbox.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "backoff==1.10.0",
        "backports-datetime-fromisoformat==1.0.0; python_version < '3.7.0'",
        "dataclasses==0.7; python_version < '3.7.0'", "ndjson==0.3.1",
        "requests>=2.22.0", "google-api-core>=1.22.1", "pydantic==1.8"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    keywords=["labelbox"],
)
