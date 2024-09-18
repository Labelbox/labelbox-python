import json

import pytest

from labelbox.data.serialization import NDJsonConverter


def test_message_task_annotation_serialization():
    with open("tests/data/assets/ndjson/mmc_import.json", "r") as file:
        data = json.load(file)

    deserialized = list(NDJsonConverter.deserialize(data))
    reserialized = list(NDJsonConverter.serialize(deserialized))

    assert data == reserialized


def test_mesage_ranking_task_wrong_order_serialization():
    with open("tests/data/assets/ndjson/mmc_import.json", "r") as file:
        data = json.load(file)

    some_ranking_task = next(
        task
        for task in data
        if task["messageEvaluationTask"]["format"] == "message-ranking"
    )
    some_ranking_task["messageEvaluationTask"]["data"]["rankedMessages"][0][
        "order"
    ] = 3

    with pytest.raises(ValueError):
        list(NDJsonConverter.deserialize([some_ranking_task]))
