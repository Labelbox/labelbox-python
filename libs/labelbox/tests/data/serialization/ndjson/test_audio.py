import labelbox.types as lb_types
from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_audio_nested_text_radio_checklist_structure():
    # Purpose: verify that class-based AudioClassificationAnnotation inputs with explicit
    # nesting serialize into v3-style nested NDJSON with:
    # - exactly three top-level groups (text_class, radio_class, checklist_class)
    # - explicit nesting via ClassificationAnnotation.classifications and ClassificationAnswer.classifications
    # - nested classifications can specify their own start_frame/end_frame (subset of root)
    # - correct field shapes per type (Text uses "value", Radio/Checklist use "name")

    # Build annotations using explicit nesting (NEW interface) matching exec/v3.py output shape
    anns = []

    # text_class: simple value without nesting
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1000,
            end_frame=1100,
            name="text_class",
            value=lb_types.Text(answer="A"),
        )
    )

    # text_class: value WITH explicit nested classifications
    # This annotation has nested classifications at the annotation level (for Text type)
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1500,
            end_frame=2400,  # Root frame range
            name="text_class",
            value=lb_types.Text(answer="text_class value"),
            classifications=[  # Explicit nesting via classifications field
                lb_types.ClassificationAnnotation(
                    name="nested_text_class",
                    start_frame=1600, end_frame=2000,  # Nested frame range (subset of root)
                    value=lb_types.Text(answer="nested_text_class value"),
                    classifications=[  # Deeper nesting
                        lb_types.ClassificationAnnotation(
                            name="nested_text_class_2",
                            start_frame=1800, end_frame=2000,  # Even more specific nested range
                            value=lb_types.Text(answer="nested_text_class_2 value")
                        )
                    ]
                ),
                lb_types.ClassificationAnnotation(
                    name="nested_text_class",
                    start_frame=2001, end_frame=2400,  # Different nested frame range
                    value=lb_types.Text(answer="nested_text_class value2")
                )
            ]
        )
    )

    # Additional text_class segments
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

    # radio_class: Explicit nesting via ClassificationAnswer.classifications
    # First segment with nested classifications
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=200,
            end_frame=1500,  # Root frame range
            name="radio_class",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(
                    name="first_radio_answer",
                    classifications=[  # Explicit nesting at answer level for Radio
                        lb_types.ClassificationAnnotation(
                            name="sub_radio_question",
                            value=lb_types.Radio(
                                answer=lb_types.ClassificationAnswer(
                                    name="first_sub_radio_answer",
                                    start_frame=1000, end_frame=1500,  # Nested frame range
                                    classifications=[  # Deeper nesting
                                        lb_types.ClassificationAnnotation(
                                            name="sub_radio_question_2",
                                            value=lb_types.Radio(
                                                answer=lb_types.ClassificationAnswer(
                                                    name="first_sub_radio_answer_2",
                                                    start_frame=1300, end_frame=1500  # Even more specific nested range
                                                )
                                            )
                                        )
                                    ]
                                )
                            )
                        ),
                        lb_types.ClassificationAnnotation(
                            name="sub_radio_question",
                            value=lb_types.Radio(
                                answer=lb_types.ClassificationAnswer(
                                    name="second_sub_radio_answer",
                                    start_frame=2100, end_frame=2500  # Nested frame range for second segment
                                )
                            )
                        )
                    ]
                )
            ),
        )
    )

    # Second segment for first_radio_answer (will merge frames in output)
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2000,
            end_frame=2500,
            name="radio_class",
            value=lb_types.Radio(
                answer=lb_types.ClassificationAnswer(
                    name="first_radio_answer",
                    classifications=[
                        lb_types.ClassificationAnnotation(
                            name="sub_radio_question",
                            value=lb_types.Radio(
                                answer=lb_types.ClassificationAnswer(
                                    name="second_sub_radio_answer"
                                )
                            )
                        )
                    ]
                )
            ),
        )
    )

    # radio_class: second_radio_answer without nesting
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

    # checklist_class: Explicit nesting via ClassificationAnswer.classifications
    # First segment with nested checklist
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=300,
            end_frame=800,  # Root frame range (first segment)
            name="checklist_class",
            value=lb_types.Checklist(
                answer=[
                    lb_types.ClassificationAnswer(
                        name="first_checklist_option",
                        classifications=[  # Explicit nesting at answer level for Checklist
                            lb_types.ClassificationAnnotation(
                                name="nested_checklist",
                                value=lb_types.Checklist(
                                    answer=[
                                        lb_types.ClassificationAnswer(
                                            name="nested_option_1",
                                            start_frame=400, end_frame=700,  # Nested frame range
                                            classifications=[  # Deeper nesting
                                                lb_types.ClassificationAnnotation(
                                                    name="checklist_nested_text",
                                                    start_frame=500, end_frame=700,  # Even more specific nested range
                                                    value=lb_types.Text(answer="checklist_nested_text value")
                                                )
                                            ]
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                ]
            ),
        )
    )

    # Second segment for first_checklist_option with different nested options
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=1200,
            end_frame=1800,  # Root frame range (second segment)
            name="checklist_class",
            value=lb_types.Checklist(
                answer=[
                    lb_types.ClassificationAnswer(
                        name="first_checklist_option",
                        classifications=[
                            lb_types.ClassificationAnnotation(
                                name="nested_checklist",
                                value=lb_types.Checklist(
                                    answer=[
                                        lb_types.ClassificationAnswer(
                                            name="nested_option_2",
                                            start_frame=1200, end_frame=1600  # Nested frame range
                                        ),
                                        lb_types.ClassificationAnswer(
                                            name="nested_option_3",
                                            start_frame=1400, end_frame=1800  # Nested frame range
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                ]
            ),
        )
    )

    # checklist_class: other options without nesting
    anns.append(
        lb_types.AudioClassificationAnnotation(
            frame=2200,
            end_frame=2900,
            name="checklist_class",
            value=lb_types.Checklist(
                answer=[
                    lb_types.ClassificationAnswer(name="second_checklist_option")
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

    # Validate text_class structure with explicit nesting and frame ranges
    text_nd = next(obj for obj in ndjson if obj["name"] == "text_class")

    # Check that we have 4 text_class answers (A, text_class value, C, D)
    assert len(text_nd["answer"]) == 4

    # Find the parent answer with nested classifications
    parent = next(
        item
        for item in text_nd["answer"]
        if item.get("value") == "text_class value"
    )
    assert parent["frames"] == [{"start": 1500, "end": 2400}]

    # Check explicit nested classifications
    nested = parent.get("classifications", [])
    assert len(nested) == 1  # One nested_text_class group
    nt = nested[0]
    assert nt["name"] == "nested_text_class"

    # Check nested_text_class has 2 answers with different frame ranges
    assert len(nt["answer"]) == 2
    nt_ans_1 = nt["answer"][0]
    assert nt_ans_1["value"] == "nested_text_class value"
    assert nt_ans_1["frames"] == [{"start": 1600, "end": 2000}]  # Nested frame range

    # Check nested_text_class_2 is nested under nested_text_class
    nt_nested = nt_ans_1.get("classifications", [])
    assert len(nt_nested) == 1
    nt2 = nt_nested[0]
    assert nt2["name"] == "nested_text_class_2"
    assert nt2["answer"][0]["value"] == "nested_text_class_2 value"
    assert nt2["answer"][0]["frames"] == [{"start": 1800, "end": 2000}]  # Even more specific nested range

    # Check second nested_text_class answer
    nt_ans_2 = nt["answer"][1]
    assert nt_ans_2["value"] == "nested_text_class value2"
    assert nt_ans_2["frames"] == [{"start": 2001, "end": 2400}]  # Different nested frame range

    # Validate radio_class structure with explicit nesting and frame ranges
    radio_nd = next(obj for obj in ndjson if obj["name"] == "radio_class")

    # Check first_radio_answer
    # Note: Segments with the same answer value are merged (both segments have "first_radio_answer")
    first_radios = [
        a for a in radio_nd["answer"] if a["name"] == "first_radio_answer"
    ]
    # We get one merged answer with both frame ranges
    assert len(first_radios) == 1
    first_radio = first_radios[0]
    # Merged frames from both segments: [200-1500] and [2000-2500]
    assert first_radio["frames"] == [{"start": 200, "end": 1500}, {"start": 2000, "end": 2500}]

    # Check explicit nested sub_radio_question
    assert "classifications" in first_radio
    sub_radio = next(
        c
        for c in first_radio["classifications"]
        if c["name"] == "sub_radio_question"
    )

    # Check sub_radio_question has 2 answers with specific frame ranges
    assert len(sub_radio["answer"]) == 2
    sr_first = next(
        a for a in sub_radio["answer"] if a["name"] == "first_sub_radio_answer"
    )
    assert sr_first["frames"] == [{"start": 1000, "end": 1500}]  # Nested frame range

    # Check sub_radio_question_2 is nested under first_sub_radio_answer
    assert "classifications" in sr_first
    sr2 = next(
        c
        for c in sr_first["classifications"]
        if c["name"] == "sub_radio_question_2"
    )
    assert sr2["answer"][0]["name"] == "first_sub_radio_answer_2"
    assert sr2["answer"][0]["frames"] == [{"start": 1300, "end": 1500}]  # Even more specific nested range

    # Check second_sub_radio_answer
    sr_second = next(
        a for a in sub_radio["answer"] if a["name"] == "second_sub_radio_answer"
    )
    # Has specific nested frame range from first segment
    assert sr_second["frames"] == [{"start": 2100, "end": 2500}]

    # Validate checklist_class structure with explicit nesting and frame ranges
    checklist_nd = next(
        obj for obj in ndjson if obj["name"] == "checklist_class"
    )

    # Check first_checklist_option
    # Note: segments with the same answer value are merged
    first_opts = [
        a
        for a in checklist_nd["answer"]
        if a["name"] == "first_checklist_option"
    ]
    assert len(first_opts) == 1
    first_opt = first_opts[0]
    # Merged frames from both segments: [300-800] and [1200-1800]
    assert first_opt["frames"] == [{"start": 300, "end": 800}, {"start": 1200, "end": 1800}]

    # Check explicit nested_checklist
    assert "classifications" in first_opt
    nested_checklist = next(
        c
        for c in first_opt["classifications"]
        if c["name"] == "nested_checklist"
    )

    # Check nested_checklist has all 3 options (nested_option_1, 2, 3) from both segments
    assert len(nested_checklist["answer"]) == 3

    # Check nested_option_1 with specific frame range
    opt1 = next(
        a for a in nested_checklist["answer"] if a["name"] == "nested_option_1"
    )
    assert opt1["frames"] == [{"start": 400, "end": 700}]  # Nested frame range

    # Check checklist_nested_text is nested under nested_option_1
    assert "classifications" in opt1
    nested_text = next(
        c
        for c in opt1["classifications"]
        if c["name"] == "checklist_nested_text"
    )
    assert nested_text["answer"][0]["value"] == "checklist_nested_text value"
    assert nested_text["answer"][0]["frames"] == [{"start": 500, "end": 700}]  # Even more specific nested range


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
