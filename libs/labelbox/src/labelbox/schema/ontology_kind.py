from enum import Enum
from typing import Optional, Union

from labelbox.schema.media_type import MediaType


class OntologyKind(Enum):
    """
    OntologyKind is an enum that represents the different types of ontologies
    """

    ModelEvaluation = "MODEL_EVALUATION"
    ResponseCreation = "RESPONSE_CREATION"
    Missing = None

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)

    @classmethod
    def get_ontology_kind_validation_error(cls, ontology_kind):
        return TypeError(
            f"{ontology_kind}: is not a valid ontology kind. Use"
            f" any of {OntologyKind.__members__.items()}"
            " from OntologyKind."
        )

    @staticmethod
    def evaluate_ontology_kind_with_media_type(
        ontology_kind, media_type: Optional[MediaType]
    ) -> Union[MediaType, None]:
        ontology_to_media = {
            OntologyKind.ModelEvaluation: (
                MediaType.Conversational,
                "For chat evaluation, media_type must be Conversational.",
            ),
            OntologyKind.ResponseCreation: (
                MediaType.Text,
                "For response creation, media_type must be Text.",
            ),
        }

        if ontology_kind in ontology_to_media:
            expected_media_type, error_message = ontology_to_media[
                ontology_kind
            ]

            if media_type is None or media_type == expected_media_type:
                media_type = expected_media_type
            else:
                raise ValueError(error_message)

        return media_type


class EditorTaskType(Enum):
    ModelChatEvaluation = "MODEL_CHAT_EVALUATION"
    ResponseCreation = "RESPONSE_CREATION"
    OfflineModelChatEvaluation = "OFFLINE_MODEL_CHAT_EVALUATION"
    Missing = None

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)

    @classmethod
    def _missing_(cls, value) -> "EditorTaskType":
        """Handle missing null new task types
        Handle upper case names for compatibility with
        the GraphQL"""

        if value is None:
            return cls.Missing

        for name, member in cls.__members__.items():
            if value == name.upper():
                return member

        return cls.Missing


class EditorTaskTypeMapper:
    @staticmethod
    def to_editor_task_type(
        ontology_kind: OntologyKind, media_type: MediaType
    ) -> EditorTaskType:
        if (
            ontology_kind
            and OntologyKind.is_supported(ontology_kind)
            and media_type
            and MediaType.is_supported(media_type)
        ):
            editor_task_type = EditorTaskTypeMapper.map_to_editor_task_type(
                ontology_kind, media_type
            )
        else:
            editor_task_type = EditorTaskType.Missing

        return editor_task_type

    @staticmethod
    def map_to_editor_task_type(
        onotology_kind: OntologyKind, media_type: MediaType
    ) -> EditorTaskType:
        if (
            onotology_kind == OntologyKind.ModelEvaluation
            and media_type == MediaType.Conversational
        ):
            return EditorTaskType.ModelChatEvaluation
        elif (
            onotology_kind == OntologyKind.ResponseCreation
            and media_type == MediaType.Text
        ):
            return EditorTaskType.ResponseCreation
        else:
            return EditorTaskType.Missing


class UploadType(Enum):
    Auto = ("AUTO",)
    Manual = ("MANUAL",)
    Missing = None

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)

    @classmethod
    def _missing_(cls, value: object) -> "UploadType":
        if value is None:
            return cls.Missing

        for name, member in cls.__members__.items():
            if value == name.upper():
                return member

        return cls.Missing
