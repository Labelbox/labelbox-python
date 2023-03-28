import abc
from typing import Any, Dict

from .feature import FeatureSchema


class BaseAnnotation(FeatureSchema, abc.ABC):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    extra: Dict[str, Any] = {}
