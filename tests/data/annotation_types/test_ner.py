from labelbox.data.annotation_types import TextEntity, DocumentEntity, DocumentTextSelection


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
