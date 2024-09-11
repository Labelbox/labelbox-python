from labelbox.data.annotation_types import (
    TextEntity,
    DocumentEntity,
    DocumentTextSelection,
)
from labelbox.data.annotation_types.ner.conversation_entity import (
    ConversationEntity,
)


def test_ner():
    start = 10
    end = 12
    text_entity = TextEntity(start=start, end=end)
    assert text_entity.start == start
    assert text_entity.end == end


def test_document_entity():
    document_entity = DocumentEntity(
        text_selections=[
            DocumentTextSelection(token_ids=["1", "2"], group_id="1", page=1)
        ]
    )

    assert document_entity.text_selections[0].token_ids == ["1", "2"]
    assert document_entity.text_selections[0].group_id == "1"
    assert document_entity.text_selections[0].page == 1


def test_conversation_entity():
    conversation_entity = ConversationEntity(message_id="1", start=0, end=1)

    assert conversation_entity.message_id == "1"
    assert conversation_entity.start == 0
    assert conversation_entity.end == 1
