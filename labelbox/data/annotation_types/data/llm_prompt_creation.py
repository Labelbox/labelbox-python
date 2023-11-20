from labelbox.typing_imports import Literal
from labelbox.utils import _NoCoercionMixin
from .base_data import BaseData


class LlmPromptCreationData(BaseData):
    class_name: Literal["LlmPromptCreationData"] = "LlmPromptCreationData"