from labelbox.typing_imports import Literal
from labelbox.utils import _NoCoercionMixin
from .base_data import BaseData


class HTMLData(BaseData, _NoCoercionMixin):
    class_name: Literal["HTMLData"] = "HTMLData"
