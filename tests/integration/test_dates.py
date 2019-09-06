from datetime import datetime, timedelta, timezone


def test_dates(client):
    project = client.create_project(name="Test")
    assert isinstance(project.created_at, datetime)
    assert isinstance(project.updated_at, datetime)

    project.update(setup_complete=datetime.now())
    assert isinstance(project.setup_complete, datetime)

    project.delete()


def test_utc_conversion(client):
    project = client.create_project(name="Test")

    # Update with a datetime without TZ info
    project.update(setup_complete=datetime.now())
    assert abs(project.setup_complete - datetime.utcnow()) < timedelta(minutes=1)

    # Update wit ha datetime with TZ info
    tz = timezone(timedelta(hours=6))
    project.update(setup_complete=datetime.now(tz))
    assert abs(project.setup_complete - datetime.utcnow()) < timedelta(minutes=1)

    project.delete()
