# Any object can be directly constuctured
# Mask(**args)
# Or we can construct arbitrary payloads without knowing their content
# E.g. AnnotationBuilder.create_region(data)
# Will dynamically create a region object (mask, poly, etc..)

# All categories will have consistent abstract interfaces so we don't need union types

# TODO: Create a from_MAL_format function that constructs these objects...

from labelbox.data.types import (
    SUPPORTED_ANNOTATION_TYPES,
    CLASSIFICATION_ALLOWING_TYPES,
)

from marshmallow.exceptions import ValidationError


from labelbox.data.region import Region
from labelbox.data.classification import (
    Classification,
)
from typing import Union


class AnnotationBuilder:
