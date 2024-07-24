from labelbox.exceptions import ResourceNotFoundError
import pytest


def test_get_labeling_service_throws_exception(project):
    with pytest.raises(ResourceNotFoundError):  # No labeling service by default
        project.get_labeling_service()
