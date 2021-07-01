from typing import Any, List, Optional, Union
from labelbox.data.annotation_types.marshmallow import required

import marshmallow_dataclass
from labelbox.data.annotation_types import \
    ClassificationAnswer


@marshmallow_dataclass.dataclass
class RadioFields:
    answer: ClassificationAnswer = required()


@marshmallow_dataclass.dataclass
class CheckListFields:
    answer: List[ClassificationAnswer] = required()


@marshmallow_dataclass.dataclass
class TextFields:
    answer: str = required()


