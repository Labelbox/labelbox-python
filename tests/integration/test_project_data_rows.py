import pytest
import uuid

from labelbox import Project, Dataset


def test_batches(project: Project, dataset: Dataset, image_url):
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ] * 2)
    task.wait_till_done()
    # TODO: Move to export_v2
    datarows = [dr.uid for dr in list(dataset.export_data_rows())]
    batch_one = f'batch one {uuid.uuid4()}'
    batch_two = f'batch two {uuid.uuid4()}'
    project.create_batch(batch_one, [datarows[0]])
    project.create_batch(batch_two, [datarows[1]])

    datarows = []
    for batch in list(project.batches()):
        datarows.extend(list(batch.export_data_rows()))

    print(datarows)
