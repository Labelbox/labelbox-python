from labelbox.data.annotation_types import TextEntity, DocumentEntity, DocumentTextSelection
from labelbox.data.annotation_types.ner.conversation_entity import ConversationEntity


def test_ner():
    start = 10
    end = 12
    text_entity = TextEntity(start=start, end=end)
    assert text_entity.start == start
    assert text_entity.end == end


def test_document_entity():
    document_entity = DocumentEntity(name="tool_name",
                                     text_selections=[
                                         DocumentTextSelection(
                                             token_ids=["1", "2"],
                                             group_id="1",
                                             page=1)
                                     ])

    assert document_entity.name == "tool_name"
    assert document_entity.text_selections[0].token_ids == ["1", "2"]
    assert document_entity.text_selections[0].group_id == "1"
    assert document_entity.text_selections[0].page == 1


def test_conversation_entity():
    document_entity = ConversationEntity(name="tool_name",
                                         message_id=1,
                                         start=0,
                                         end=1,
                                         confidence=0.5)

    assert document_entity.name == "tool_name"
    assert document_entity.message_id == "1"
    assert document_entity.start == 0
    assert document_entity.end == 1
    assert document_entity.confidence == 0.5