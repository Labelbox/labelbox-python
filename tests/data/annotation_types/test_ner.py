from labelbox.data.annotation_types import TextEntity, DocumentEntity, DocumentTextSelection


def test_ner():
    start = 10
    end = 12
    text_entity = TextEntity(start=start, end=end)
    assert text_entity.start == start
    assert text_entity.end == end

def test_document_entity():
    document_entity = DocumentEntity(name="tool_name", textSelections=[DocumentTextSelection(tokenIds=["1", "2"], groupId="1", page=1)])

    assert document_entity.name == "tool_name"
    assert document_entity.textSelections[0].tokenIds == ["1", "2"]
    assert document_entity.textSelections[0].groupId == "1"
    assert document_entity.textSelections[0].page == 1