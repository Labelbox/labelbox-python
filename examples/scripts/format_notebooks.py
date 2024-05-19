import glob
import json
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
import string

from yapf.yapflib.yapf_api import FormatCode

IGNORE = ["template.ipynb"]

BANNER_CELL = {
    "cell_type": "markdown",
    "id": "db768cda",
    "metadata": {},
    "source": [
        "<td>",
        '   <a target="_blank" href="https://labelbox.com" ><img src="https://labelbox.com/blog/content/images/2021/02/logo-v4.svg" width=256/></a>',
        "</td>",
    ],
}

LINK_CELL = {
    "cell_type": "markdown",
    "id": "cb5611d0",
    "metadata": {},
    "source": [
        "<td>",
        '<a href="{colab}" target="_blank"><img',
        'src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>',
        "</td>",
        "\n",
        "<td>",
        '<a href="{github}" target="_blank"><img',
        'src="https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white" alt="GitHub"></a>',
        "</td>",
    ],
}

COLAB_TEMPLATE = "https://colab.research.google.com/github/Labelbox/labelbox-python/blob/develop/examples/{filename}"
GITHUB_TEMPLATE = "https://github.com/Labelbox/labelbox-python/tree/develop/examples/{filename}"


def format_cell(source):
    for line in source.split("\n"):
        if line.strip().startswith(("!", "%")):
            return source.replace("!", "%")
    return FormatCode(source, style_config="google")[0]


def add_headers(file_name):
    with open(file_name, "r") as file:
        data = json.load(file)

    colab_path = COLAB_TEMPLATE.format(filename=file_name)
    github_path = GITHUB_TEMPLATE.format(filename=file_name)

    link_cell = deepcopy(LINK_CELL)

    link_cell["source"][1] = link_cell["source"][1].format(colab=colab_path)
    link_cell["source"][6] = link_cell["source"][6].format(github=github_path)

    data["cells"] = [BANNER_CELL, link_cell] + data["cells"]

    with open(file_name, "w") as file:
        file.write(json.dumps(data, indent=4))

    print("Formatted", file_name)


def format_file(file_name):
    with open(file_name, "r") as file:
        data = json.load(file)

    colab_path = COLAB_TEMPLATE.format(filename=file_name)
    github_path = GITHUB_TEMPLATE.format(filename=file_name)

    link_cell = deepcopy(LINK_CELL)

    link_cell["source"][1] = link_cell["source"][1].format(colab=colab_path)
    link_cell["source"][6] = link_cell["source"][6].format(github=github_path)

    data["cells"] = [BANNER_CELL, link_cell] + data["cells"][2:]

    for cell in data["cells"]:
        if cell["cell_type"] == "code":
            if isinstance(cell["source"], list):
                cell["source"] = "".join(cell["source"])
            cell["source"] = format_cell(cell["source"])
            if cell["source"].endswith("\n"):
                cell["source"] = cell["source"][:-1]

    with open(file_name, "w") as file:
        file.write(json.dumps(data, indent=4))
    print("Formatted", file_name)


if __name__ == "__main__":
    files = [
        file
        for file in glob.glob("**/*.ipynb", recursive=True)
        if file.split("/")[-1] not in IGNORE
    ]
    with ProcessPoolExecutor(10) as pool:
        pool.map(format_file, files)
