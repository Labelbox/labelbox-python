import labelbox.types as lb_types
from labelbox.data.serialization import NDJsonConverter


def test_serialize_label():
    prompt_text_annotation = lb_types.PromptClassificationAnnotation(
        feature_schema_id="ckrb1sfkn099c0y910wbo0p1a",
        name="test",
        extra={"uuid": "test"},
        value=lb_types.PromptText(
            answer="the answer to the text questions right here"
        ),
    )

    prompt_text_ndjson = {
        "answer": "the answer to the text questions right here",
        "name": "test",
        "schemaId": "ckrb1sfkn099c0y910wbo0p1a",
        "dataRow": {"id": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
        "uuid": "test",
    }

    data_gen_label = lb_types.Label(
        data={"uid": "ckrb1sf1i1g7i0ybcdc6oc8ct"},
        annotations=[prompt_text_annotation],
    )
    serialized_label = next(NDJsonConverter().serialize([data_gen_label]))

    assert serialized_label == prompt_text_ndjson
