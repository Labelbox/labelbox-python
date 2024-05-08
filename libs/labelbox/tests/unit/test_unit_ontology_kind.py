from labelbox.schema.ontology_kind import OntologyKind, EditorTaskType, EditorTaskTypeMapper
from labelbox.schema.media_type import MediaType


def test_ontology_kind_conversions_from_editor_task_type():
    ontology_kind = OntologyKind.ModelEvaluation
    media_type = MediaType.Conversational
    editor_task_type = EditorTaskTypeMapper.to_editor_task_type(
        ontology_kind, media_type)
    assert editor_task_type == EditorTaskType.ModelChatEvaluation

    ontology_kind = OntologyKind.Missing
    media_type = MediaType.Image
    editor_task_type = EditorTaskTypeMapper.to_editor_task_type(
        ontology_kind, media_type)
    assert editor_task_type == EditorTaskType.Missing

    ontology_kind = OntologyKind.ModelEvaluation
    media_type = MediaType.Video
    editor_task_type = EditorTaskTypeMapper.to_editor_task_type(
        ontology_kind, media_type)
    assert editor_task_type == EditorTaskType.Missing
