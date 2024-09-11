import time
from labelbox import Project
from labelbox.schema.identifiables import GlobalKeys, UniqueIds


def test_get_task_queue(project: Project):
    task_queues = project.task_queues()
    assert len(task_queues) == 3
    review_queue = next(
        tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE"
    )
    assert review_queue


def test_get_overview_no_details(project: Project):
    po = project.get_overview()

    assert isinstance(po.to_label, int)
    assert isinstance(po.in_review, int)
    assert isinstance(po.in_rework, int)
    assert isinstance(po.skipped, int)
    assert isinstance(po.done, int)
    assert isinstance(po.issues, int)
    assert isinstance(po.labeled, int)
    assert isinstance(po.total_data_rows, int)


def test_get_overview_with_details(project: Project):
    po = project.get_overview(details=True)

    assert isinstance(po.to_label, int)
    assert isinstance(po.in_review["data"], list)
    assert isinstance(po.in_review["total"], int)
    assert isinstance(po.in_rework["data"], list)
    assert isinstance(po.in_rework["total"], int)
    assert isinstance(po.skipped, int)
    assert isinstance(po.done, int)
    assert isinstance(po.issues, int)
    assert isinstance(po.labeled, int)
    assert isinstance(po.total_data_rows, int)


def _validate_moved(project, queue_name, data_row_count):
    timeout_seconds = 30
    sleep_time = 2
    while True:
        task_queues = project.task_queues()
        review_queue = next(
            tq for tq in task_queues if tq.queue_type == queue_name
        )

        if review_queue.data_row_count == data_row_count:
            break

        if timeout_seconds <= 0:
            raise AssertionError(
                "Timed out expecting data_row_count of 1 in the review queue"
            )

        timeout_seconds -= sleep_time
        time.sleep(sleep_time)


def test_move_to_task(configured_batch_project_with_label):
    project, _, data_row, _ = configured_batch_project_with_label
    task_queues = project.task_queues()

    review_queue = next(
        tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE"
    )
    project.move_data_rows_to_task_queue([data_row.uid], review_queue.uid)
    _validate_moved(project, "MANUAL_REVIEW_QUEUE", 1)

    review_queue = next(
        tq for tq in task_queues if tq.queue_type == "MANUAL_REWORK_QUEUE"
    )
    project.move_data_rows_to_task_queue(
        GlobalKeys([data_row.global_key]), review_queue.uid
    )
    _validate_moved(project, "MANUAL_REWORK_QUEUE", 1)

    review_queue = next(
        tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE"
    )
    project.move_data_rows_to_task_queue(
        UniqueIds([data_row.uid]), review_queue.uid
    )
    _validate_moved(project, "MANUAL_REVIEW_QUEUE", 1)
