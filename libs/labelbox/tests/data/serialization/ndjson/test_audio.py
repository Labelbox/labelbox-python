import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_audio_nested_text_radio_checklist_structure():
    # Purpose: verify that class-based AudioClassificationAnnotation inputs serialize
    # into v3-style nested NDJSON with:
    # - exactly three top-level groups (text_class, radio_class, checklist_class)
    # - children nested only under their closest containing parent frames
    # - correct field shapes per type (Text uses "value", Radio/Checklist use "name")

    # Build annotations mirroring exec/v3.py shapes using class-based annotations
    anns = []

    # text_class top-level with multiple values
    # Expect: produces an NDJSON object named "text_class" with four answer entries;
    # the long segment (1500-2400) will carry nested children below.
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1000,
            end_frame=1100,
            name="text_class",
            value=lb_types.Text(answer="A"),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1500,
            end_frame=2400,
            name="text_class",
            value=lb_types.Text(answer="text_class value"),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2500,
            end_frame=2700,
            name="text_class",
            value=lb_types.Text(answer="C"),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2900,
            end_frame=2999,
            name="text_class",
            value=lb_types.Text(answer="D"),
        )
    )

    # nested under text_class
    # Expect: nested_text_class (1600-2000) nests under the 1500-2400 parent;
    # nested_text_class_2 nests under nested_text_class only (no duplicates at parent level).
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1600,
            end_frame=2000,
            name="nested_text_class",
            value=lb_types.Text(answer="nested_text_class value"),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1800,
            end_frame=2000,
            name="nested_text_class_2",
            value=lb_types.Text(answer="nested_text_class_2 value"),
        )
    )

    # radio_class top-level
    # Expect: two answer entries for first_radio_answer (two frame segments) and
    # two for second_radio_answer; children attach only to their closest container answer.
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=200,
            end_frame=1500,
            name="radio_class",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(name="first_radio_answer")
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2000,
            end_frame=2500,
            name="radio_class",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(name="first_radio_answer")
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1550,
            end_frame=1700,
            name="radio_class",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(name="second_radio_answer")
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2700,
            end_frame=3000,
            name="radio_class",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(name="second_radio_answer")
            ),
        )
    )

    # nested radio
    # Expect: sub_radio_question nests under first_radio_answer (1000-1500), and
    # sub_radio_question_2 nests under sub_radio_question's first_sub_radio_answer only.
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1000,
            end_frame=1500,
            name="sub_radio_question",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(
                    name="first_sub_radio_answer"
                )
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1300,
            end_frame=1500,
            name="sub_radio_question_2",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(
                    name="first_sub_radio_answer_2"
                )
            ),
        )
    )

    # checklist_class top-level
    # Expect: three answer entries (first/second/third_checklist_option) and
    # nested checklist children attach to the first option segments where contained.
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=300,
            end_frame=800,
            name="checklist_class",
            value=lb_types.Checklist(
                answer=[
                    lb_types.ClassificationAnswer(name="first_checklist_option")
                ]
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1200,
            end_frame=1800,
            name="checklist_class",
            value=lb_types.Checklist(
                answer=[
                    lb_types.ClassificationAnswer(name="first_checklist_option")
                ]
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2200,
            end_frame=2900,
            name="checklist_class",
            value=lb_types.Checklist(
                answer=[
                    lb_types.ClassificationAnswer(
                        name="second_checklist_option"
                    )
                ]
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2500,
            end_frame=3500,
            name="checklist_class",
            value=lb_types.Checklist(
                answer=[
                    lb_types.ClassificationAnswer(name="third_checklist_option")
                ]
            ),
        )
    )

    # nested checklist
    # Expect: nested_checklist options 1/2/3 attach to their containing parent frames;
    # checklist_nested_text attaches under nested_option_1 only.
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=400,
            end_frame=700,
            name="nested_checklist",
            value=lb_types.Checklist(
                answer=[lb_types.ClassificationAnswer(name="nested_option_1")]
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1200,
            end_frame=1600,
            name="nested_checklist",
            value=lb_types.Checklist(
                answer=[lb_types.ClassificationAnswer(name="nested_option_2")]
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1400,
            end_frame=1800,
            name="nested_checklist",
            value=lb_types.Checklist(
                answer=[lb_types.ClassificationAnswer(name="nested_option_3")]
            ),
        )
    )
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=500,
            end_frame=700,
            name="checklist_nested_text",
            value=lb_types.Text(answer="checklist_nested_text value"),
        )
    )

    # Serialize a single Label containing all of the above annotations
    label = lb_types.Label(
        data={"global_key": "audio_nested_test_key"}, annotations=anns
    )
    ndjson = list(NDJsonConverter.serialize([label]))

    # Assert: exactly three top-level groups, matching v3 root objects
    assert {obj["name"] for obj in ndjson} == {
        "text_class",
        "radio_class",
        "checklist_class",
    }

    # Validate text_class structure: children appear under the long segment only,
    # and grandchildren only under their immediate parent
    text_nd = next(obj for obj in ndjson if obj["name"] == "text_class")
    parent = next(
        item
        for item in text_nd["answer"]
        if item.get("value") == "text_class value"
    )
    nested = parent.get("classifications", [])
    names = {c["name"] for c in nested}
    assert "nested_text_class" in names
    nt = next(c for c in nested if c["name"] == "nested_text_class")
    nt_ans = nt["answer"][0]
    assert nt_ans["value"] == "nested_text_class value"
    nt_nested = nt_ans.get("classifications", [])
    assert any(c["name"] == "nested_text_class_2" for c in nt_nested)

    # Validate radio_class structure and immediate-child only
    radio_nd = next(obj for obj in ndjson if obj["name"] == "radio_class")
    first_radio = next(
        a for a in radio_nd["answer"] if a["name"] == "first_radio_answer"
    )
    assert any(
        c["name"] == "sub_radio_question"
        for c in first_radio.get("classifications", [])
    )
    # sub_radio_question_2 is nested under sub_radio_question only
    sub_radio = next(
        c
        for c in first_radio["classifications"]
        if c["name"] == "sub_radio_question"
    )
    sr_first = next(
        a for a in sub_radio["answer"] if a["name"] == "first_sub_radio_answer"
    )
    assert any(
        c["name"] == "sub_radio_question_2"
        for c in sr_first.get("classifications", [])
    )

    # Validate checklist_class structure: nested_checklist exists, and nested text
    # appears only under nested_option_1 (closest container)
    checklist_nd = next(
        obj for obj in ndjson if obj["name"] == "checklist_class"
    )
    first_opt = next(
        a
        for a in checklist_nd["answer"]
        if a["name"] == "first_checklist_option"
    )
    assert any(
        c["name"] == "nested_checklist"
        for c in first_opt.get("classifications", [])
    )
    nested_checklist = next(
        c
        for c in first_opt["classifications"]
        if c["name"] == "nested_checklist"
    )
    # Ensure nested text present under nested_checklist → nested_option_1
    opt1 = next(
        a for a in nested_checklist["answer"] if a["name"] == "nested_option_1"
    )
    assert any(
        c["name"] == "checklist_nested_text"
        for c in opt1.get("classifications", [])
    )


def test_audio_top_level_only_basic():
    anns = [
        lb_types.AudioClassificationAnnotation(
            frame=200,
            end_frame=1500,
            name="radio_class",
            value=lb_types.Radio(answer=lb_types.ClassificationAnswer(name="first_radio_answer")),
        ),
        lb_types.AudioClassificationAnnotation(
            frame=1550,
            end_frame=1700,
            name="radio_class",
            value=lb_types.Radio(answer=lb_types.ClassificationAnswer(name="second_radio_answer")),
        ),
        lb_types.AudioClassificationAnnotation(
            frame=1200,
            end_frame=1800,
            name="checklist_class",
            value=lb_types.Checklist(answer=[lb_types.ClassificationAnswer(name="angry")]),
        ),
    ]

    label = lb_types.Label(data={"global_key": "audio_top_level_only"}, annotations=anns)
    ndjson = list(NDJsonConverter.serialize([label]))

    names = {o["name"] for o in ndjson}
    assert names == {"radio_class", "checklist_class"}

    radio = next(o for o in ndjson if o["name"] == "radio_class")
    r_answers = sorted(radio["answer"], key=lambda x: x["frames"][0]["start"]) 
    assert r_answers[0]["name"] == "first_radio_answer"
    assert r_answers[0]["frames"] == [{"start": 200, "end": 1500}]
    assert "classifications" not in r_answers[0]
    assert r_answers[1]["name"] == "second_radio_answer"
    assert r_answers[1]["frames"] == [{"start": 1550, "end": 1700}]
    assert "classifications" not in r_answers[1]

    checklist = next(o for o in ndjson if o["name"] == "checklist_class")
    c_answers = checklist["answer"]
    assert len(c_answers) == 1
    assert c_answers[0]["name"] == "angry"
    assert c_answers[0]["frames"] == [{"start": 1200, "end": 1800}]
    assert "classifications" not in c_answers[0]
