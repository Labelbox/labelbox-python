import pytest


def test_issues_export(project):
    exported_issues_url = project.export_issues()
    assert exported_issues_url

    exported_issues_url = project.export_issues("Open")
    assert exported_issues_url
    assert "?status=Open" in exported_issues_url

    exported_issues_url = project.export_issues("Resolved")
    assert exported_issues_url
    assert "?status=Resolved" in exported_issues_url

    invalidStatusValue = "Closed"
    with pytest.raises(ValueError) as exc_info:
        exported_issues_url = project.export_issues(invalidStatusValue)
    assert "status must be in" in str(exc_info.value)
    assert "Found %s" % (invalidStatusValue) in str(exc_info.value)
