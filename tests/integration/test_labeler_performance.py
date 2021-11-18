from datetime import datetime, timezone, timedelta
import time
import pytest


def test_labeler_performance(label_pack):
    project, dataset, data_row, label = label_pack
    # Sleep a bit as it seems labeler performance isn't updated immediately.
    time.sleep(10)

    labeler_performance = list(project.labeler_performance())
    assert len(labeler_performance) == 1
    my_performance = labeler_performance[0]
    assert my_performance.user == project.client.get_user()
    assert my_performance.count == 1
    assert isinstance(my_performance.last_activity_time, datetime)
    now_utc = datetime.now().astimezone(timezone.utc)
    assert timedelta(0) < now_utc - my_performance.last_activity_time < \
        timedelta(seconds=30)
