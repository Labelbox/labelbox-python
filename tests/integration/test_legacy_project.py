import pytest

from labelbox.exceptions import InvalidQueryError, MalformedQueryException
from labelbox.schema.media_type import MediaType
from labelbox.schema.queue_mode import QueueMode


def test_project_dataset(client, rand_gen):
    with pytest.raises(
            MalformedQueryException,
            match=
            "DataSet queue mode is deprecated. Please prefer Batch queue mode."
    ):
        client.create_project(
            name=rand_gen(str),
            queue_mode=QueueMode.Dataset,
        )


def test_legacy_project_dataset_relationships(project, dataset):

    assert [ds for ds in project.datasets()] == []
    assert [p for p in dataset.projects()] == []
