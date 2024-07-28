from labelbox.typing_imports import Literal
from .base_data import BaseData


class ConversationData(BaseData):
    class_name: Literal["ConversationData"] = "ConversationData"