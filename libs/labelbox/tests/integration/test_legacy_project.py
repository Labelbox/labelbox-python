from os import name

import pytest
from pydantic import ValidationError

from labelbox.schema import media_type
from labelbox.schema.media_type import MediaType


def test_project_auto_audit_parameters(client, rand_gen):
    with pytest.raises(
        ValueError,
        match="quality_modes must be set instead of auto_audit_percentage or auto_audit_number_of_labels.",
    ):
        client.create_project(
            name=rand_gen(str),
            media_type=MediaType.Image,
            auto_audit_percentage=0.5,
        )

    with pytest.raises(
        ValidationError,
        match="quality_modes must be set instead of auto_audit_percentage or auto_audit_number_of_labels.",
    ):
        client.create_project(
            name=rand_gen(str),
            media_type=MediaType.Image,
            auto_audit_number_of_labels=2,
        )


def test_project_name_parameter(client, rand_gen):
    with pytest.raises(
        ValidationError, match="project name must be a valid string"
    ):
        client.create_project(name="     ", media_type=MediaType.Image)
