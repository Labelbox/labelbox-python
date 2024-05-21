import pandas
import glob
from collections import defaultdict
from pprint import pprint

"""
Script used to generate readme programmatically works by taking the links of all the notebooks
then dividing them to different tables based on directory name. Pandas is used to make the tables. Using inline HTML to support our doc page. 
"""

IGNORE = ["template.ipynb"]

ORDER = [
    "basics",
    "exports",
    "project_configuration",
    "annotation_import",
    "integrations",
    "model_experiments",
    "prediction_upload",
]

SDK_EXAMPLE_HEADER = """
# Labelbox SDK Examples\n
- Learn how to use the SDK by following along\n
- Run in google colab, view the notebooks on github, or clone the repo and run locally\n
"""

README_EXAMPLE_HEADER = """---
title: Python tutorials
---

"""

COLAB_TEMPLATE = "https://colab.research.google.com/github/Labelbox/labelbox-python/blob/develop/examples/{filename}"
GITHUB_TEMPLATE = "https://github.com/Labelbox/labelbox-python/tree/develop/examples/{filename}"


def create_header(link: str) -> str:
    """Creates headers of tables with h2 tags to support readme docs

    Args:
        link (str): file path

    Returns:
        str: formatted file path for header
    """
    # Splits up link uses directory name
    split_link = link.split("/")[0].replace("_", " ").split(" ")
    header = []

    # Capitalize first letter of each word
    for word in split_link:
        header.append(word.capitalize())
    return f"<h2>{' '.join(header)}</h2>"


def create_title(link: str) -> str:
    """Create notebook titles will be name of notebooks with _ replaced with spaces and file extension removed

    Args:
        link (str): file path

    Returns:
        str: formatted file path for notebook title
    """
    split_link = link.split(".")[-2].split("/")[-1].replace("_", " ").split(" ")
    title = []

    # List to lower case certain words and list to keep certain acronyms capitalized
    lower_case_words = ["to"]
    acronyms = ["html", "pdf", "llm", "dicom", "sam"]

    for word in split_link:
        if word.lower() in acronyms:
            title.append(word.upper())
        elif word.lower() in lower_case_words:
            title.append(word.lower())
        else:
            title.append(word.capitalize())
    return " ".join(title).split(".")[0]


def make_link(link: str, photo: str, link_type: str) -> str:
    """Creates the links for the notebooks as an anchor tag

    Args:
        link (str): file path
        photo (str): photo link
        link_type (str): type of link (github, google colab)

    Returns:
        str: anchor tag with image
    """
    return f'<a href="{link}" target="_blank"><img src="{photo}" alt="Open In {link_type}"></a>'


def make_links_dict(links: str):
    """Creates dictionary needed for pandas to generate the table takes all the links and makes each directory its own table

    Args:
        links (list[str]): list of links to notebooks from glob

    Returns:
        defaultdict[list]: returns dict that is in pandas dataFrame format
    """
    link_dict = defaultdict(list)
    extra_links = []
    for section in ORDER:
        link_dict[section] = []
    for link in links:
        if link.split("/")[-1] in IGNORE:
            continue
        if link.split("/")[0] == "extras":
            extra_links.append(link)
        else:
            split_link = link.split("/")[0]
            link_dict[split_link].append(link)
    link_dict["Extras"] = extra_links
    return link_dict


def make_table(base: str) -> str:
    """main function to make table

    Args:
        base (str): Header of file generated. Defaults to an empty string.

    Returns:
        str: markdown string file
    """
    link_dict = make_links_dict(glob.glob("**/*.ipynb", recursive=True))
    generated_markdown = base
    for link_list in link_dict.values():
        pandas_dict = {"Notebook": [], "Github": [], "Google Colab": []}
        generated_markdown += f"{create_header(link_list[0])}\n\n"
        for link in link_list:
            pandas_dict["Notebook"].append(create_title(link))
            pandas_dict["Github"].append(
                make_link(
                    GITHUB_TEMPLATE.format(filename="/".join(link.split("/"))),
                    "https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white",
                    "Github",
                )
            )
            pandas_dict["Google Colab"].append(
                make_link(
                    COLAB_TEMPLATE.format(filename="/".join(link.split("/"))),
                    "https://colab.research.google.com/assets/colab-badge.svg",
                    "Colab",
                )
            )
        df = pandas.DataFrame(pandas_dict)
        generated_markdown += f"{df.to_html(col_space={'Notebook':400}, index=False, escape=False, justify='left')}\n\n"
    return f"{generated_markdown.rstrip()}\n"


def main(github: bool):
    """
    Args:
        github (bool): if this is the readme for github.
    """
    if github:
        with open("./README.md", "w") as readme:
            readme.write(make_table(SDK_EXAMPLE_HEADER))
    else:
        with open("./tutorials.html", "w") as readme:
            readme.write(make_table(README_EXAMPLE_HEADER))


if __name__ == "__main__":
    main(True)
