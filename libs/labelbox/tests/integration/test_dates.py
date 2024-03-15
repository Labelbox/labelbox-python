from datetime import datetime, timedelta, timezone


def test_dates(project):
    assert isinstance(project.created_at, datetime)
    assert isinstance(project.updated_at, datetime)

    project.update(setup_complete=datetime.now())
    assert isinstance(project.setup_complete, datetime)


def test_utc_conversion(project):
    assert isinstance(project.created_at, datetime)
    assert project.created_at.tzinfo == timezone.utc

    # Update with a datetime without TZ info.
    project.update(setup_complete=datetime.now())
    # Check that the server-side, UTC date is the same as local date
    # converted locally to UTC.
    diff = project.setup_complete - datetime.now().astimezone(timezone.utc)
    assert abs(diff) < timedelta(minutes=1)

    # Update with a datetime with TZ info
    tz = timezone(timedelta(hours=6))  # +6 timezone
    project.update(setup_complete=datetime.utcnow().replace(tzinfo=tz))
    diff = datetime.utcnow() - project.setup_complete.replace(tzinfo=None)
    assert diff > timedelta(hours=5, minutes=58)
