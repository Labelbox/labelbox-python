import json

from labelbox.data.annotation_types.data.generic_data_row_data import (
    GenericDataRowData,
)
import pytest

from labelbox.data.serialization import NDJsonConverter
from labelbox.types import (
    Label,
    MessageEvaluationTaskAnnotation,
    MessageSingleSelectionTask,
    MessageMultiSelectionTask,
    MessageInfo,
    OrderedMessageInfo,
    MessageRankingTask,
)


def test_message_task_annotation_serialization():
    with open("tests/data/assets/ndjson/mmc_import.json", "r") as file:
        data = json.load(file)

    labels = [
        Label(
            data=GenericDataRowData(
                uid="cnjencjencjfencvj",
            ),
            annotations=[
                MessageEvaluationTaskAnnotation(
                    name="single-selection",
                    extra={"uuid": "c1be3a57-597e-48cb-8d8d-a852665f9e72"},
                    value=MessageSingleSelectionTask(
                        message_id="clxfzocbm00083b6v8vczsept",
                        model_config_name="GPT 5",
                        parent_message_id="clxfznjb800073b6v43ppx9ca",
                    ),
                )
            ],
        ),
        Label(
            data=GenericDataRowData(
                uid="cfcerfvergerfefj",
            ),
            annotations=[
                MessageEvaluationTaskAnnotation(
                    name="multi-selection",
                    extra={"uuid": "gferf3a57-597e-48cb-8d8d-a8526fefe72"},
                    value=MessageMultiSelectionTask(
                        parent_message_id="clxfznjb800073b6v43ppx9ca",
                        selected_messages=[
                            MessageInfo(
                                message_id="clxfzocbm00083b6v8vczsept",
                                model_config_name="GPT 5",
                            )
                        ],
                    ),
                )
            ],
        ),
        Label(
            data=GenericDataRowData(
                uid="cwefgtrgrthveferfferffr",
            ),
            annotations=[
                MessageEvaluationTaskAnnotation(
                    name="ranking",
                    extra={"uuid": "hybe3a57-5gt7e-48tgrb-8d8d-a852dswqde72"},
                    value=MessageRankingTask(
                        parent_message_id="clxfznjb800073b6v43ppx9ca",
                        ranked_messages=[
                            OrderedMessageInfo(
                                message_id="clxfzocbm00083b6v8vczsept",
                                model_config_name="GPT 4 with temperature 0.7",
                                order=1,
                            ),
                            OrderedMessageInfo(
                                message_id="clxfzocbm00093b6vx4ndisub",
                                model_config_name="GPT 5",
                                order=2,
                            ),
                        ],
                    ),
                )
            ],
        ),
    ]

    res = list(NDJsonConverter.serialize(labels))

    assert res == data


def test_mesage_ranking_task_wrong_order_serialization():
    with pytest.raises(ValueError):
        (
            Label(
                data=GenericDataRowData(
                    uid="cwefgtrgrthveferfferffr",
                ),
                annotations=[
                    MessageEvaluationTaskAnnotation(
                        name="ranking",
                        extra={
                            "uuid": "hybe3a57-5gt7e-48tgrb-8d8d-a852dswqde72"
                        },
                        value=MessageRankingTask(
                            parent_message_id="clxfznjb800073b6v43ppx9ca",
                            ranked_messages=[
                                OrderedMessageInfo(
                                    message_id="clxfzocbm00093b6vx4ndisub",
                                    model_config_name="GPT 5",
                                    order=1,
                                ),
                                OrderedMessageInfo(
                                    message_id="clxfzocbm00083b6v8vczsept",
                                    model_config_name="GPT 4 with temperature 0.7",
                                    order=1,
                                ),
                            ],
                        ),
                    )
                ],
            ),
        )
