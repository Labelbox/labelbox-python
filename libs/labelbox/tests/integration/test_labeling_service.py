import pytest

from labelbox.exceptions import ResourceNotFoundError
from labelbox.schema.labeling_service import LabelingService, LabelingServiceStatus


def test_get_labeling_service_throws_exception(project):
    with pytest.raises(ResourceNotFoundError):  # No labeling service by default
        project.get_labeling_service()


def test_start_labeling_service(project):
    labeling_service = LabelingService.start(project.client, project.uid)
    assert labeling_service.status == LabelingServiceStatus.SetUp
    assert labeling_service.project_id == project.uid

    # Check that the labeling service is now available
    labeling_service = project.get_labeling_service()
    assert labeling_service.status == LabelingServiceStatus.SetUp
    assert labeling_service.project_id == project.uid
