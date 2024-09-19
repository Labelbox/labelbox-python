from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..feature_schema import FeatureSchema
from ..mixins import ConfidenceMixin, CustomMetricsMixin

if TYPE_CHECKING:
    from .classification_annotation import ClassificationAnnotation

from pydantic import Field


class ClassificationAnswer(FeatureSchema, ConfidenceMixin, CustomMetricsMixin):
    """
    - Represents a classification option.
    - Because it inherits from FeatureSchema
        the option can be represented with either the name or feature_schema_id

    - The keyframe arg only applies to video classifications.
      Each answer can have a keyframe independent of the others.
        So unlike object annotations, classification annotations
          track keyframes at a classification answer level.
    """

    extra: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    keyframe: Optional[bool] = None
    classifications: Optional[List["ClassificationAnnotation"]] = None
