from labelbox.typing_imports import Literal
from labelbox.utils import _NoCoercionMixin
from .base_data import BaseData


class ConversationData(BaseData):
    class_name: Literal["ConversationData"] = "ConversationData"