from enum import Enum


class EditorTaskType(Enum):
    ModelEvaluationWithUploadedAsset = "MODEL_EVALUATION_WITH_UPLOADED_ASSET",
    ResponseCreation = "RESPONSE_CREATION",
    ModelChatEvaluation = "MODEL_CHAT_EVALUATION"

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)

    @classmethod
    def get_media_type_validation_error(cls, editor_task_type):
        return TypeError(f"{editor_task_type}: is not a valid media type. Use"
                         f" any of {EditorTaskType.__members__.items()}"
                         " from EditorTaskType.")
