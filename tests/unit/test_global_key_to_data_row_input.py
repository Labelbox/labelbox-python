from labelbox.schema.global_key import AssignGlobalKeyToDataRowInput


def test_global_key_to_data_row_input():
    """Test that the AssignGlobalKeyToDataRowInput class can be instantiated
    with a valid data_row_id and global_key.
    """
    data_row_id = "cl7asgri20yvo075b4vtfedjb"
    global_key = "123cl7cqkdmk000iu0p1hltbb1fb"
    assignment_input = AssignGlobalKeyToDataRowInput(data_row_id=data_row_id,
                                                     global_key=global_key)
    assert assignment_input.data_row_id == data_row_id
    assert assignment_input.global_key == global_key
