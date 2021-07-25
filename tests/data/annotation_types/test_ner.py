from labelbox.data.annotation_types import TextEntity


def test_ner():
    start = 10
    end = 12
    text_entity = TextEntity(start=start, end=end)
    assert text_entity.start == start
    assert text_entity.end == end
