from labelbox.schema.task_assignment_status import TaskAssignmentStatus


def test_bulk_assign_data_rows(
    configured_batch_project_with_label, project_based_user
):
    project, _, data_row, _ = configured_batch_project_with_label
    user = project_based_user

    result = project.bulk_assign_data_rows(
        user_id=user.uid,
        data_row_ids=[data_row.uid],
    )
    assert result is True


def test_bulk_assign_data_rows_with_allowed_statuses(
    configured_batch_project_with_label, project_based_user
):
    project, _, data_row, _ = configured_batch_project_with_label
    user = project_based_user

    result = project.bulk_assign_data_rows(
        user_id=user.uid,
        data_row_ids=[data_row.uid],
        allowed_statuses=[
            TaskAssignmentStatus.FREE,
            TaskAssignmentStatus.RESERVED,
        ],
    )
    assert result is True


def test_bulk_assign_empty_list(configured_batch_project_with_label):
    project, _, _, _ = configured_batch_project_with_label

    result = project.bulk_assign_data_rows(
        user_id="any_user_id",
        data_row_ids=[],
    )
    assert result is True
