from labelbox.schema.global_key import AssignGlobalKeyToDataRowInput

import uuid


def test_assign_global_keys_to_data_rows(client, dataset, image_url):
    """Test that the assign_global_keys_to_data_rows method can be called
    with a valid list of AssignGlobalKeyToDataRowInput objects.
    """

    dr_1 = dataset.create_data_row(row_data=image_url, external_id="hello")
    dr_2 = dataset.create_data_row(row_data=image_url, external_id="world")
    row_ids = set([dr_1.uid, dr_2.uid])

    gk_1 = str(uuid.uuid4())
    gk_2 = str(uuid.uuid4())

    assignment_inputs = [
        AssignGlobalKeyToDataRowInput(data_row_id=dr_1.uid, global_key=gk_1),
        AssignGlobalKeyToDataRowInput(data_row_id=dr_2.uid, global_key=gk_2)
    ]
    client.assign_global_keys_to_data_rows(assignment_inputs)

    res = client.get_data_row_ids_for_global_keys([gk_1, gk_2])

    assert len(res) == 2
    successful_assignments = set(a['id'] for a in res)
    assert successful_assignments == row_ids
