from typing import Any, List, Optional, Union

import marshmallow_dataclass
from labelbox.data.annotation_types.classification.classification import Classification
from labelbox.data.annotation_types.marshmallow import RequiredFieldMixin, required

from typing import Any, List, Optional, Union
from labelbox.data.annotation_types.marshmallow import required, default_none
import marshmallow_dataclass

class ClassificationAnswer:
    # TODO: Only one of these is required for now ....
    value: str = default_none()
    schema_id: str = default_none()

@marshmallow_dataclass.dataclass
class Classification(RequiredFieldMixin):
    name: str = (
        required()
    )
    schema_id: str = (
        required()
    )
    answer: Union[str, ClassificationAnswer, List[ClassificationAnswer]]
    classifications: List[Union["Radio", "CheckList", "Text", "Dropdown"]] = required()

@marshmallow_dataclass.dataclass
class Radio(Classification):
    answer: ClassificationAnswer = required()

    def to_mal_ndjson(self):
        return {"answer" : {
                "schemaId" : self.answer.schema_id # TODO: This also can be set by name...
            }}

    def to_mal_subclass_ndjson(self):
        ### We need to get the schema id if the feature was provided by name ...
        # TODO: Warn if there are any subclassifications. MAL will ignore
        return {
            "schemaId" : self.schema_id,
           ** self.to_mal_ndjson()
        }

@marshmallow_dataclass.dataclass
class CheckList(Classification):
    answer: List[ClassificationAnswer] = required()

    def to_mal_ndjson(self):
        return {
            # answer.schema_id isn't guarenteed to exist because it can be set by name
            "answer" : [ {"schemaId" : answer.schema_id} for answer in self.answer]
        }

    def to_mal_subclass_ndjson(self):
        ### We need to get the schema id if the feature was provided by name ...
        # TODO: Warn if there are any subclassifications. MAL will ignore
        return {
            "schemaId" : self.schema_id,
            **self.to_mal_ndjson()
        }

@marshmallow_dataclass.dataclass
class Text(Classification):
    answer: str = required()

    def to_mal_ndjson(self):
        return {"answer" : self.text}

    def to_mal_subclass_ndjson(self):
        ### We need to get the schema id if the feature was provided by name ...
        # TODO: Warn if there are any subclassifications. MAL will ignore
        return {
            "schemaId" : self.schema_id,
            ** self.to_mal_ndjson()
        }


@marshmallow_dataclass.dataclass
class Dropdown(Classification):
    answer: List[ClassificationAnswer] = required()

    def to_mal_ndjson(self):
        raise NotImplementedError("MAL Does not support the dropdown tool at this time")

    def to_mal_subclass_ndjson(self):
        self.to_mal_ndjson()
