from datetime import datetime, timezone, timedelta
import time


IMG_URL = "https://picsum.photos/200/300"


def test_labeler_performance(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    assert list(project.labeler_performance()) == []

    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    label = project.create_label(data_row=data_row, label="test",
                                 seconds_to_label=0.0)
    # Sleep a bit as it seems labeler performance isn't updated immediately.
    time.sleep(5)

    labeler_performance = list(project.labeler_performance())
    assert len(labeler_performance) == 1
    my_performance = labeler_performance[0]
    assert my_performance.user == client.get_user()
    assert my_performance.count == 1
    assert isinstance(my_performance.last_activity_time, datetime)
    now_utc = datetime.now().astimezone(timezone.utc)
    assert timedelta(0) < now_utc - my_performance.last_activity_time < \
        timedelta(seconds=30)
