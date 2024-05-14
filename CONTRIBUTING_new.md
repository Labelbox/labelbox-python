# Contribution Guide

## Our Contribution Goals
We appreciate every contribution. This guide is designed to facilitate easy contributions from SDK users, AI engineers, machine-learning engineers, and software developers in the following areas:

- **Notebooks (Examples):** Implement practical use cases and solutions other can use too.
- **Code Documentation:** Enhance documentation within this repository, including docstrings and code comments.
- **Test Cases:** Develop tests to ensure code reliability.
- **Bug Fixes:** Help to identify and resolve issues.
- **Feature Improvements:** Optimize and enhance current functionalities.
- **New Features and Extensions:** Innovate and expand our capabilities.

Additional Ways to Contribute:

- Bug Reporting: Help us identify issues.
- Suggestions for Improvements: Propose ways to enhance our tools.
- Feature Requests: Let us know what additional functionalities you’d like to see.

We look forward to your contributions!

## Notebooks
Our notebooks contain practical examples for labelbox sdk uses. To update a notebook, 
- Creating a new issue you will address or assign an existing issue to yourself here https://github.com/Labelbox/labelbox-python/issues
- Create a new branch using our <branch naming guidelines>
- Update or create a new notebook <notebook development process>
- Test your changes
- Submit a PR <create a PR template>
- Merge code: use default github button (or labelbox engineer may merge it too)

## Code documentation
- Create a new branch using our <branch naming guidelines>
- Update code documentation <code documentation update process>
- Submit a PR <create a PR template>
- Merge code: use default github button (or labelbox engineer may merge it too)

## Test cases
- Create a new branch using our <branch naming guidelines>
- Implement or update a new test <testing guidelines>
- Submit a PR <create a PR template>
- Merge code: use default github button (or labelbox engineer may merge it too)

## Bug fixing
- Creating a new issue you will address or assign an existing issue to yourself here https://github.com/Labelbox/labelbox-python/issues
- Create a new branch using our <branch naming guidelines>
- Implement a fix
- If necessary, add a unit or an integration test <testing guidelines>
- Update code documentation <code documentation update process>
- Submit a PR <create a PR template>
- Merge code: use default github button (or labelbox engineer may merge it too)

## Feature optimization / improvements
- Creating a new issue you will address or assign an existing issue to yourself here https://github.com/Labelbox/labelbox-python/issues
- Create a new branch using our <branch naming guidelines>
- Implement a code update <coding guidelines / naming conventions>
- Add or update a unit or an integration test <testing guidelines>
- Update code documentation <code documentation update process>
- Submit a PR <create a PR template>
- Merge code: use default github button (or labelbox engineer may merge it too)

## New Features and Extensions
- Coming up in the future


## Helpful steps
### Branches and Tags
* Begin by creating a branch off the develop branch.
* All development should occur in feature branches, ideally prefixed with the contributor's initials. For example, use `fs/feature_name` for a feature branch.
* Once a PR is approved, merge it into the develop branch using the standard GitHub _PR merge button_   s labeled Merge pull request. This action will squash all commits.
* Ensure that you review all comments thoroughly and make necessary edits or deletions before completing the merge.



### Internal Code Documentation Update

Our internal developer documentation is generated from Python docstrings and hosted on [ReadTheDocs](https://readthedocs.org/projects/labelbox-python/) using Sphinx.

Docstrings should be formatted according to the guidelines found [here](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html).

Unless you're adding a new package or file, documentation updates are automated. You can review your updated documentation by running the following command at the root of the repository:
```bash
rye run docs
```

After running the command, navigate to `docs/build/html` and open the index.html file to confirm that your documentation updates are reflected:
```bash
open index.html
```

**Adding New Packages:**
If you add a new package, you must update the Sphinx configuration:
* Add the new package to docs/labelbox/index.rst.
* Create a new .rst file for the new package.

Re-run the documentation command to generate the updated docs and verify your changes.
