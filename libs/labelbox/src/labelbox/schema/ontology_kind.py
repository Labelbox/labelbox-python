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
        return TypeError(f"{ontology_kind}: is not a valid ontology kind. Use"
                         f" any of {OntologyKind.__members__.items()}"
                         " from OntologyKind.")
    
    @staticmethod
    def evaluate_ontology_kind_with_media_type(ontology_kind,
                                               media_type: Union[MediaType, None]) -> Union[MediaType, None]:
        
        if ontology_kind and ontology_kind is OntologyKind.ModelEvaluation:
            if media_type is None:
                media_type = MediaType.Conversational
            else:
                if media_type is not MediaType.Conversational:
                    raise ValueError(
                        "For chat evaluation, media_type must be Conversational."
                    )
        
        elif ontology_kind == OntologyKind.ResponseCreation:
            if media_type is None:
                media_type = MediaType.Text
            else:
                if media_type is not MediaType.Text:
                    raise ValueError(
                        "For response creation, media_type must be Text."
                    )
                    
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
    def _missing_(cls, value) -> 'EditorTaskType':
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
    def to_editor_task_type(ontology_kind: OntologyKind,
                            media_type: MediaType) -> EditorTaskType:
        if ontology_kind and OntologyKind.is_supported(
                ontology_kind) and media_type and MediaType.is_supported(
                    media_type):
            editor_task_type = EditorTaskTypeMapper.map_to_editor_task_type(
                ontology_kind, media_type)
        else:
            editor_task_type = EditorTaskType.Missing

        return editor_task_type

    @staticmethod
    def map_to_editor_task_type(onotology_kind: OntologyKind,
                                media_type: MediaType) -> EditorTaskType:
        if onotology_kind == OntologyKind.ModelEvaluation and media_type == MediaType.Conversational:
            return EditorTaskType.ModelChatEvaluation
        elif onotology_kind == OntologyKind.ResponseCreation and media_type == MediaType.Text:
            return EditorTaskType.ResponseCreation
        else:
            return EditorTaskType.Missing


class UploadType(Enum):
    Auto = 'AUTO',
    Manual = 'MANUAL',
    Missing = None

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)

    @classmethod
    def _missing_(cls, value: object) -> 'UploadType':
        if value is None:
            return cls.Missing

        for name, member in cls.__members__.items():
            if value == name.upper():
                return member

        return cls.Missing
