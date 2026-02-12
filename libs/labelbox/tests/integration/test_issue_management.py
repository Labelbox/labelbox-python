"""Integration tests for issue management (Issues, Comments, Issue Categories).

Uses a single Image project with one data row to test the full CRUD
lifecycle, keeping setup cost minimal.
"""

import time

from labelbox import Project
from labelbox.schema.issue import Issue, IssueStatus, Comment
from labelbox.schema.issue_category import IssueCategory
from labelbox.schema.issue_position import ImageIssuePosition


# ---------------------------------------------------------------------------
# Issue Category CRUD
# ---------------------------------------------------------------------------


def test_create_issue_category(project: Project):
    category = project.create_issue_category(
        name="Quality", description="Quality-related issues"
    )
    assert isinstance(category, IssueCategory)
    assert category.id is not None
    assert category.name == "Quality"
    assert category.description == "Quality-related issues"

    # Cleanup
    category.delete()


def test_get_issue_categories(project: Project):
    cat1 = project.create_issue_category(
        name="Cat A", description="First category"
    )
    cat2 = project.create_issue_category(
        name="Cat B", description="Second category"
    )

    categories = project.get_issue_categories()
    cat_ids = {c.id for c in categories}
    assert cat1.id in cat_ids
    assert cat2.id in cat_ids

    # Cleanup
    cat1.delete()
    cat2.delete()


def test_update_issue_category(project: Project):
    category = project.create_issue_category(
        name="Original", description="Original description"
    )
    updated = category.update(name="Renamed", description="New description")
    assert updated.name == "Renamed"
    assert updated.description == "New description"

    # Cleanup
    updated.delete()


def test_delete_issue_category(project: Project):
    category = project.create_issue_category(
        name="ToDelete", description="Will be deleted"
    )
    assert category.delete() is True


# ---------------------------------------------------------------------------
# Issue CRUD
# ---------------------------------------------------------------------------


def test_create_issue(project: Project, data_row):
    issue = project.create_issue(
        content="Something is wrong here",
        data_row_id=data_row.uid,
    )
    assert isinstance(issue, Issue)
    assert issue.id is not None
    assert issue.content == "Something is wrong here"
    assert issue.status == IssueStatus.OPEN
    assert issue.data_row_id == data_row.uid
    assert issue.created_by is not None

    # Cleanup
    issue.delete()


def test_create_issue_with_position(project: Project, data_row):
    position = ImageIssuePosition(x=100, y=200)
    issue = project.create_issue(
        content="Pin on image",
        data_row_id=data_row.uid,
        position=position,
    )
    assert issue.position is not None

    # Cleanup
    issue.delete()


def test_create_issue_with_category(project: Project, data_row):
    category = project.create_issue_category(
        name="Test Category", description="For testing"
    )
    issue = project.create_issue(
        content="Categorized issue",
        data_row_id=data_row.uid,
        category_id=category.id,
    )
    assert issue.category_id == category.id

    # Verify lazy-loaded category
    fetched_cat = issue.category()
    assert fetched_cat is not None
    assert fetched_cat.id == category.id

    # Cleanup
    issue.delete()
    category.delete()


def test_get_issue(project: Project, data_row):
    created = project.create_issue(
        content="Fetch me",
        data_row_id=data_row.uid,
    )
    fetched = project.get_issue(created.id)
    assert fetched.id == created.id
    assert fetched.content == "Fetch me"

    # Cleanup
    created.delete()


def test_get_issues(configured_project_with_label):
    # get_issues() only returns issues that have a label_id (backend
    # filters out labelId IS NULL), so we must attach a label.
    project, _dataset, data_row, label = configured_project_with_label

    issue1 = project.create_issue(
        content="First issue",
        data_row_id=data_row.uid,
        label_id=label.uid,
    )
    issue2 = project.create_issue(
        content="Second issue",
        data_row_id=data_row.uid,
        label_id=label.uid,
    )

    # Allow eventual consistency in the backend index
    for _ in range(5):
        issues = list(project.get_issues())
        issue_ids = {i.id for i in issues}
        if issue1.id in issue_ids and issue2.id in issue_ids:
            break
        time.sleep(2)

    assert issue1.id in issue_ids
    assert issue2.id in issue_ids

    # Cleanup
    project.delete_issues([issue1.id, issue2.id])


def test_get_issues_with_status_filter(configured_project_with_label):
    # get_issues() only returns issues that have a label_id (backend
    # filters out labelId IS NULL), so we must attach a label.
    project, _dataset, data_row, label = configured_project_with_label

    issue = project.create_issue(
        content="Filter test",
        data_row_id=data_row.uid,
        label_id=label.uid,
    )

    # Allow eventual consistency in the backend index
    for _ in range(5):
        open_issues = list(project.get_issues(status=IssueStatus.OPEN))
        if any(i.id == issue.id for i in open_issues):
            break
        time.sleep(2)

    assert any(i.id == issue.id for i in open_issues)

    # Give the backend a moment to ensure the index is consistent
    # for the next query
    time.sleep(2)

    resolved_issues = list(project.get_issues(status=IssueStatus.RESOLVED))
    assert not any(i.id == issue.id for i in resolved_issues)

    # Cleanup
    issue.delete()


def test_update_issue(project: Project, data_row):
    issue = project.create_issue(
        content="Original content",
        data_row_id=data_row.uid,
    )
    updated = issue.update(content="Updated content")
    assert updated.content == "Updated content"

    # Cleanup
    updated.delete()


def test_resolve_and_reopen_issue(project: Project, data_row):
    issue = project.create_issue(
        content="Resolve me",
        data_row_id=data_row.uid,
    )
    resolved = issue.resolve()
    assert resolved.status == IssueStatus.RESOLVED
    assert resolved.resolved_by is not None

    reopened = resolved.reopen()
    assert reopened.status == IssueStatus.OPEN

    # Cleanup
    reopened.delete()


def test_delete_issue(project: Project, data_row):
    issue = project.create_issue(
        content="Delete me",
        data_row_id=data_row.uid,
    )
    assert issue.delete() is True


def test_delete_issues_bulk(project: Project, data_row):
    issue1 = project.create_issue(
        content="Bulk delete 1",
        data_row_id=data_row.uid,
    )
    issue2 = project.create_issue(
        content="Bulk delete 2",
        data_row_id=data_row.uid,
    )
    assert project.delete_issues([issue1.id, issue2.id]) is True


# ---------------------------------------------------------------------------
# Issue accessor methods
# ---------------------------------------------------------------------------


def test_issue_data_row(project: Project, data_row):
    issue = project.create_issue(
        content="Data row test",
        data_row_id=data_row.uid,
    )
    fetched_dr = issue.data_row()
    assert fetched_dr is not None
    assert fetched_dr.uid == data_row.uid

    # Cleanup
    issue.delete()


# ---------------------------------------------------------------------------
# Comment CRUD
# ---------------------------------------------------------------------------


def test_create_comment(project: Project, data_row):
    issue = project.create_issue(
        content="Comment test",
        data_row_id=data_row.uid,
    )
    comment = issue.create_comment(content="This is a comment")
    assert isinstance(comment, Comment)
    assert comment.id is not None
    assert comment.content == "This is a comment"
    assert comment.created_by is not None

    # Cleanup
    issue.delete()


def test_get_comments(project: Project, data_row):
    issue = project.create_issue(
        content="Multi-comment test",
        data_row_id=data_row.uid,
    )
    comment1 = issue.create_comment(content="Comment 1")
    comment2 = issue.create_comment(content="Comment 2")

    comments = issue.comments()
    comment_ids = {c.id for c in comments}
    assert comment1.id in comment_ids
    assert comment2.id in comment_ids

    # Cleanup
    issue.delete()


def test_update_comment(project: Project, data_row):
    issue = project.create_issue(
        content="Update comment test",
        data_row_id=data_row.uid,
    )
    comment = issue.create_comment(content="Original comment")
    updated = comment.update(content="Revised comment")
    assert updated.content == "Revised comment"

    # Cleanup
    issue.delete()


def test_delete_comment(project: Project, data_row):
    issue = project.create_issue(
        content="Delete comment test",
        data_row_id=data_row.uid,
    )
    comment = issue.create_comment(content="Will be deleted")
    assert comment.delete() is True

    # Verify comment is gone
    remaining = issue.comments()
    assert not any(c.id == comment.id for c in remaining)

    # Cleanup
    issue.delete()
