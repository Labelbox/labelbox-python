import pytest
from pydantic import ValidationError

from labelbox.schema.media_type import MediaType


def test_project_name_parameter(client, rand_gen):
    with pytest.raises(
        ValidationError, match="project name must be a valid string"
    ):
        client.create_project(name="     ", media_type=MediaType.Image)
