import pandas
import glob
from collections import defaultdict

SDK_EXAMPLE_HEADER = """
# Labelbox SDK Examples\n
- Learn how to use the SDK by following along\n
- Run in google colab, view the notebooks on github, or clone the repo and run locally\n
"""

COLAB_TEMPLATE = "https://colab.research.google.com/github/Labelbox/labelbox-python/blob/develop/examples/{filename}"
GITHUB_TEMPLATE = (
    "https://github.com/Labelbox/labelbox-python/tree/develop/examples/{filename}"
)

def create_header(link: str) -> str:
    """Creates headers of tables with h2 tags to support readme

    Args:
        link (str): file path

    Returns:
        str: formatted file path for header
    """
    # Splits up link uses directory name
    split_link = link.split("/")[1].replace("_", " ").split(" ")
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
    """Creates the actually links to the notebooks

    Args:
        link (str): file path
        photo (str): _description_
        link_type (str): _description_

    Returns:
        str: _description_
    """
    return f"<a href=\"{link}\" target=\"_blank\"><img src=\"{photo}\" alt=\"Open In {link_type}\" onclick=\"(function prevent(e){{e.preventDefault()}}()\"></a>"


def make_links_dict(links):
    link_dict = defaultdict(list)
    for link in links:
        split_link = link.split("/")[1]
        link_dict[split_link].append(link)
    return link_dict

def make_table(base):
    link_dict = make_links_dict(glob.glob("**/examples/**/*.ipynb", recursive=True))
    generated_markdown = base
    for link_list in link_dict.values():
        pandas_dict = {"Notebook": [], "Github": [], "Google Colab": []}
        generated_markdown += f"{create_header(link_list[0])}\n\n"
        for link in link_list:
            pandas_dict["Notebook"].append(create_title(link))
            pandas_dict["Github"].append(make_link(GITHUB_TEMPLATE.format(filename = '/'.join(link.split('/')[1:])),"https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white", "Github"))
            pandas_dict["Google Colab"].append(make_link(COLAB_TEMPLATE.format(filename='/'.join(link.split('/')[1:])), "https://colab.research.google.com/assets/colab-badge.svg", "Colab"))
        df = pandas.DataFrame(pandas_dict)
        generated_markdown += f"{df.to_html(col_space={'Notebook':400},index=False, escape=False, justify='left')}\n\n"
    return generated_markdown

with open("./examples/README.md", "w") as readme:
    readme.write(f"{make_table(SDK_EXAMPLE_HEADER).rstrip()}\n")