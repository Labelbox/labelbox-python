from typing import Any, List, Optional, Union

import marshmallow_dataclass
from labelbox.data.annotation_types.classification_fields import (
    CheckListFields, RadioFields, TextFields)
from labelbox.data.annotation_types.video import \
    VideoSupported
from labelbox.data.types import \
    ClassificationAnswer
from labelbox_pkgs.prediction_import_lib.utils.marshmallow import (
    BaseSchema, default_none, required)



class Classification:
    answer: Union[str, ClassificationAnswer, List[ClassificationAnswer]]
    # TODO: Figure out how to support recursion..
    #classifications: List[Union["RadioSubclass", "CheckListSubclass", "TextSubclass"]] = required()
    # Does 'Any' with post_load logic work?


@marshmallow_dataclass.dataclass
class Classification(Classification):
    name: str = (
        required()
    )
    schema_id: str = (
        required()
    )


@marshmallow_dataclass.dataclass
class RadioSubclass(RadioFields, SubClassification):
    ...

@marshmallow_dataclass.dataclass
class CheckListSubclass(CheckListFields, SubClassification):
    ...

@marshmallow_dataclass.dataclass
class TextSubclass(TextFields, SubClassification):
    ...

