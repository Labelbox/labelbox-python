import time

from labelbox import Project


def test_get_task_queue(project: Project):
    task_queues = project.task_queues()
    assert len(task_queues) == 3
    review_queue = next(
        tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE")
    assert review_queue


def test_move_to_task(configured_batch_project_with_label: Project):
    project, _, data_row, label = configured_batch_project_with_label
    task_queues = project.task_queues()

    review_queue = next(
        tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE")
    project.move_data_rows_to_task_queue([data_row.uid], review_queue.uid)

    timeout_seconds = 30
    sleep_time = 2
    while True:
        task_queues = project.task_queues()
        review_queue = next(
            tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE")

        if review_queue.data_row_count == 1:
            break

        if timeout_seconds <= 0:
            raise AssertionError(
                "Timed out expecting data_row_count of 1 in the review queue")

        timeout_seconds -= sleep_time
        time.sleep(sleep_time)
