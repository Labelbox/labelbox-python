import pytest
import requests
from labelbox import Dataset
from labelbox.exceptions import ResourceNotFoundError, MalformedQueryException, InvalidQueryError
from labelbox.schema.dataset import MAX_DATAROW_PER_API_OPERATION


def test_dataset(client, rand_gen):

    # confirm dataset can be created
    name = rand_gen(str)
    dataset = client.create_dataset(name=name)
    assert dataset.name == name
    assert dataset.created_by() == client.get_user()
    assert dataset.organization() == client.get_organization()

    retrieved_dataset = client.get_dataset(dataset.uid)
    assert retrieved_dataset.name == dataset.name
    assert retrieved_dataset.uid == dataset.uid
    assert retrieved_dataset.created_by() == dataset.created_by()
    assert retrieved_dataset.organization() == dataset.organization()

    dataset = client.get_dataset(dataset.uid)
    assert dataset.name == name

    new_name = rand_gen(str)
    dataset.update(name=new_name)
    # Test local object updates.
    assert dataset.name == new_name

    # Test remote updates.
    dataset = client.get_dataset(dataset.uid)
    assert dataset.name == new_name

    # Test description
    description = rand_gen(str)
    assert dataset.description == ""
    dataset.update(description=description)
    assert dataset.description == description

    dataset.delete()

    with pytest.raises(ResourceNotFoundError):
        dataset = client.get_dataset(dataset.uid)


def test_dataset_filtering(client, rand_gen):
    name_1 = rand_gen(str)
    name_2 = rand_gen(str)
    d1 = client.create_dataset(name=name_1)
    d2 = client.create_dataset(name=name_2)

    assert list(client.get_datasets(where=Dataset.name == name_1)) == [d1]
    assert list(client.get_datasets(where=Dataset.name == name_2)) == [d2]

    d1.delete()
    d2.delete()


def test_get_data_row_for_external_id(dataset, rand_gen, image_url):
    external_id = rand_gen(str)

    with pytest.raises(ResourceNotFoundError):
        data_row = dataset.data_row_for_external_id(external_id)

    data_row = dataset.create_data_row(row_data=image_url,
                                       external_id=external_id)

    found = dataset.data_row_for_external_id(external_id)
    assert found.uid == data_row.uid
    assert found.external_id == external_id

    dataset.create_data_row(row_data=image_url, external_id=external_id)
    assert len(dataset.data_rows_for_external_id(external_id)) == 2

    task = dataset.create_data_rows(
        [dict(row_data=image_url, external_id=external_id)])
    task.wait_till_done()
    assert len(dataset.data_rows_for_external_id(external_id)) == 3


def test_upload_video_file(dataset, sample_video: str) -> None:
    """
    Tests that a mp4 video can be uploaded and preserve content length
    and content type.

    """
    dataset.create_data_row(row_data=sample_video)
    task = dataset.create_data_rows([sample_video, sample_video])
    task.wait_till_done()

    with open(sample_video, 'rb') as video_f:
        content_length = len(video_f.read())

    for data_row in dataset.data_rows():
        url = data_row.row_data
        response = requests.head(url, allow_redirects=True)
        assert int(response.headers['Content-Length']) == content_length
        assert response.headers['Content-Type'] == 'video/mp4'


def test_create_pdf(dataset):
    dataset.create_data_row(
        row_data={
            "pdfUrl":
                "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/sample-document-1.pdf",
            "textLayerUrl":
                "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/sample-document-custom-text-layer.json"
        })
    dataset.create_data_row(row_data={
        "pdfUrl":
            "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/sample-document-1.pdf",
        "textLayerUrl":
            "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/sample-document-custom-text-layer.json"
    },
                            media_type="PDF")

    with pytest.raises(InvalidQueryError):
        # Wrong media type
        dataset.create_data_row(row_data={
            "pdfUrl":
                "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/sample-document-1.pdf",
            "textLayerUrl":
                "https://lb-test-data.s3.us-west-1.amazonaws.com/document-samples/sample-document-custom-text-layer.json"
        },
                                media_type="TEXT")


def test_bulk_conversation(dataset, sample_bulk_conversation: list) -> None:
    """
    Tests that bulk conversations can be uploaded.

    """
    task = dataset.create_data_rows(sample_bulk_conversation)
    task.wait_till_done()

    assert len(list(dataset.data_rows())) == len(sample_bulk_conversation)


def test_data_row_export(dataset, image_url):
    n_data_rows = 5
    ids = set()
    for _ in range(n_data_rows):
        ids.add(dataset.create_data_row(row_data=image_url))
    result = list(dataset.export_data_rows())
    assert len(result) == n_data_rows
    assert set(result) == ids


@pytest.mark.parametrize('data_rows', [5], indirect=True)
def test_dataset_export_v2(export_v2_test_helpers, dataset, data_rows):
    data_row_ids = [dr.uid for dr in data_rows]
    params = {"performance_details": False, "label_details": False}
    task_results = export_v2_test_helpers.run_dataset_export_v2_task(
        dataset, params=params)
    assert len(task_results) == 5
    assert set([dr['data_row']['id'] for dr in task_results
               ]) == set(data_row_ids)


@pytest.mark.parametrize('data_rows', [5], indirect=True)
def test_dataset_export_v2_datarow_list(export_v2_test_helpers, dataset,
                                        data_rows):
    datarow_filter_size = 2
    data_row_ids = [dr.uid for dr in data_rows]

    params = {"performance_details": False, "label_details": False}
    filters = {"data_row_ids": data_row_ids[:datarow_filter_size]}

    task_results = export_v2_test_helpers.run_dataset_export_v2_task(
        dataset, filters=filters, params=params)

    # only 2 datarows should be exported
    assert len(task_results) == datarow_filter_size
    # only filtered datarows should be exported
    assert set([dr['data_row']['id'] for dr in task_results
               ]) == set(data_row_ids[:datarow_filter_size])


def test_create_descriptor_file(dataset):
    import unittest.mock as mock
    with mock.patch.object(dataset.client,
                           'upload_data',
                           wraps=dataset.client.upload_data) as upload_data_spy:
        dataset._create_descriptor_file(items=[{'row_data': 'some text...'}])
        upload_data_spy.assert_called()
        call_args, call_kwargs = upload_data_spy.call_args_list[0][
            0], upload_data_spy.call_args_list[0][1]
        assert call_args == ('[{"row_data": "some text..."}]',)
        assert call_kwargs == {
            'content_type': 'application/json',
            'filename': 'json_import.json'
        }


def test_max_dataset_datarow_upload(dataset, image_url, rand_gen):
    external_id = str(rand_gen)
    items = [dict(row_data=image_url, external_id=external_id)
            ] * (MAX_DATAROW_PER_API_OPERATION + 1)

    with pytest.raises(MalformedQueryException):
        dataset.create_data_rows(items)
