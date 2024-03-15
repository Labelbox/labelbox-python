from datetime import datetime, timezone, timedelta
import pytest
import os


@pytest.mark.skipif(
    condition=os.environ['LABELBOX_TEST_ENVIRON'] == "onprem",
    reason="longer runtime than expected for onprem. unskip when resolved.")
def test_labeler_performance(configured_project_with_label):
    project, _, _, _ = configured_project_with_label

    labeler_performance = list(project.labeler_performance())
    assert len(labeler_performance) == 1
    my_performance = labeler_performance[0]
    assert my_performance.user == project.client.get_user()
    assert my_performance.count == 1
    assert isinstance(my_performance.last_activity_time, datetime)
    now_utc = datetime.now().astimezone(timezone.utc)
    assert timedelta(0) < now_utc - my_performance.last_activity_time < \
        timedelta(seconds=60)
