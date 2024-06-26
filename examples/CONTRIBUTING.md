# Contribution guide

Thank you for contributing to our notebook examples! To ensure that your contribution aligns with our guidelines, please carefully review the following guide.

## Table of contents

- [General notebook requirements](#general-notebook-requirements)
- [Branches and tags](#branches-and-tags)
- [Github workflows](#github-workflows)
- [General prerequisites](#general-prerequisites)
- [Styling tools](#styling-tools)

## General notebook requirements

Review our [template notebook](template.ipynbs) for general overview on how notebooks should be structure. The template notebook and this section just serves as a guide and exceptions can be made. Here are our general requirements:

1. Ensure that any modified notebooks run when edited.
2. Ensure that you update any relevant headers and comments within the code block you may add or change.
3. Notebooks should start with a top header below the Labelbox and link icons with the title of the notebook as a main header **#** and a overview of what the notebook shows.
4. Use "labelbox[data]" over labelbox for installs to ensure you have the correct dependencies.
5. Imports and installs should come after the main header under a **Setup** section.
6. Labelbox and other platforms with clients and API keys should be specified under a single section.
7. Subsections need a second level header **##** and an overview of the section.
8. The last cell should be a clean up section to delete any labelbox objects created and commented out to prevent accidentally running code blocks.
9. Notebook github action [workflows](#github-workflows) are required to run successfully before merging.

> [!IMPORTANT]
> Please make sure to remove any API keys before pushing changes

## Branches and tags

- All development happens in feature branches ideally prefixed by contributor's initials. For example `fs/feature_name`.
- Approved PRs are merged to the `develop` branch.
- All releases align to a git tag.

## Github workflows

- Github Branch Workflow
  - When you push to a branch that contains files inside the examples directory, it will automatically reformat your notebook to match our given style and provide appropriate headers. Once this workflow is completed it will commit back to your branch which then you can pull.
  - If your push contains new notebooks or modifies the names of notebooks the readme will be updated to reflect the change with updated links.

## General prerequisites

[Rye](https://rye-up.com/) may be installed before contributing to the repository as it is the tool used to style our example notebooks. This could be used to avoid the github styling workflow. This is also the packaging tool used for the main SDK. The pyproject used for the example notebooks is a virtual package and does not get published.

## Styling tools

Rye is setup in this directory to use a customs script that will run the notebooks through our formatting tools and create readmes.

- `rye sync` in the examples folder to install the correct dev dependencies.
- `rye run clean` runs a series of formatting tools.
- `rye run create-readme` creates a readme based off our notebooks.
