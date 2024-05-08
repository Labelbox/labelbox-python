from enum import Enum
from typing import Optional

from labelbox.schema.media_type import MediaType


class OntologyKind(Enum):
    """
    OntologyKind is an enum that represents the different types of ontologies
    At the moment it is only limited to ModelEvaluation
    """
    ModelEvaluation = "MODEL_EVALUATION"
    Missing = None

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)

    @classmethod
    def get_ontology_kind_validation_error(cls, ontology_kind):
        return TypeError(f"{ontology_kind}: is not a valid ontology kind. Use"
                         f" any of {OntologyKind.__members__.items()}"
                         " from OntologyKind.")


class EditorTaskType(Enum):
    ModelChatEvaluation = "MODEL_CHAT_EVALUATION"
    Missing = None

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls)


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
        else:
            return EditorTaskType.Missing
