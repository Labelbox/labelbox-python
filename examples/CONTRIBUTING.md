# Contribution Guide

Thank you for contributing to our notebook examples! To ensure that your contribution aligns with our guidelines, please carefully review the following guide.

## Table of Contents

- [General Guidelines](#general-guidelines)
- [Branches and Tags](#branches-and-tags)
- [Github Workflows](#github-workflows)
- [General Prerequisites](#general-prerequisites)
- [Styling Tools](#styling-tools)
- [General Notebook Requirements](#general-notebook-requirements)

## General Guidelines

* Ensure that any modified notebooks run when edited.
* Ensure that you update any relevant headers and comments within the code block you may add or change.

## Branches and Tags

* All development happens in feature branches ideally prefixed by contributor's initials. For example `fs/feature_name`.
* Approved PRs are merged to the `develop` branch.
* All releases align to a git tag.

## Github Workflows

* Github Branch Workflow
  * When you push to a branch that contains files inside the examples directory, it will automatically reformat your notebook to match our given style and provide appropriate headers. Once this workflow is completed it will commit back to your branch which then you can then pull.
  * If your push contains new notebooks or modifies the names of notebooks the readme will be updated to reflect the change with updated links

## General Prerequisites

[Rye](https://rye-up.com/) may be installed before contributing to the repository as it is the tool used to style our example notebooks. This could be used to avoid the github styling workflow. This is also the packaging tool used for the main SDK. The pyproject used for the example notebooks is a virtual package and does not get published. 

## Styling Tools

Rye is setup in this directory to use a customs script that will run the notebooks through our formatting tools and create readmes.

* `rye sync` in the examples folder to install the correct dev dependencies.
* `rye run clean` runs a series of formatting tools.
* `rye run create-readme` creates a readme based off our notebooks.

# General Notebook Requirements

Review our [template notebook](https://github.com/Labelbox/labelbox-python/blob/develop/examples/template.ipynb) for general overview on how notebooks should be structure. This notebook and section just serves as a guide and exception can be made. Here are our general requirements:
 
1. Notebooks should start with a top header below the Labelbox and link icons with the title of the notebook as a main header "#" and a overview of what the notebook shows
2. Use "labelbox[data]" over labelbox for installs to ensure you have the correct dependencies.
3. Imports and installs should come after the main header under a Setup section
4. Labelbox and other platform with clients API keys should be specified under a single section.
5. Subsections need a second level header "##".
6. Subsections includes an overview of the section does any links to our docs.
7. The last cell should be a clean up section to delete any labelbox objects created.
