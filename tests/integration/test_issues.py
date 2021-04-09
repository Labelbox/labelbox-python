import pytest


def test_issues_export(project):
    exported_issues_url = project.export_issues()
    assert exported_issues_url is not None
    assert exported_issues_url is not ''

    exported_issues_url = project.export_issues("Open")
    assert exported_issues_url is not None
    assert exported_issues_url is not ''
    assert "?status=Open" in exported_issues_url

    exported_issues_url = project.export_issues("Resolved")
    assert exported_issues_url is not None
    assert exported_issues_url is not ''
    assert "?status=Resolved" in exported_issues_url

    invalidStatusValue = "Closed"
    with pytest.raises(ValueError) as exc_info:
        exported_issues_url = project.export_issues(invalidStatusValue)
    assert str(
        exc_info.value
    ) == "status must be in [None, 'Open', 'Resolved']. Found {}".format(
        invalidStatusValue)
