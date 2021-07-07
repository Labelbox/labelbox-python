from typing import Any, List, Union, ForwardRef

from pydantic.main import BaseModel

from labelbox.data.annotation_types.reference import FeatureSchemaRef

# Requires 3.7+
Subclass = ForwardRef('Subclass')

class ClassificationAnswer(FeatureSchemaRef):
    ...


class Radio(BaseModel):
    answer: ClassificationAnswer

    def to_mal_ndjson(self):
        return {
            "answer": {
                "schemaId":
                    self.answer.
                    schema_id  # TODO: This also can be set by name...
            }
        }

    def to_mal_subclass_ndjson(self):
        ### We need to get the schema id if the feature was provided by name ...
        # TODO: Warn if there are any subclassifications. MAL will ignore
        return {"schemaId": self.schema_id, **self.to_mal_ndjson()}


class CheckList(BaseModel):
    answer: List[ClassificationAnswer]

    def to_mal_ndjson(self):
        return {
            # answer.schema_id isn't guarenteed to exist because it can be set by name
            "answer": [{
                "schemaId": answer.schema_id
            } for answer in self.answer]
        }

    def to_mal_subclass_ndjson(self):
        ### We need to get the schema id if the feature was provided by name ...
        # TODO: Warn if there are any subclassifications. MAL will ignore
        return {"schemaId": self.schema_id, **self.to_mal_ndjson()}


class Text(BaseModel):
    answer: str

    def to_mal_ndjson(self):
        return {"answer": self.text}

    def to_mal_subclass_ndjson(self):
        ### We need to get the schema id if the feature was provided by name ...
        # TODO: Warn if there are any subclassifications. MAL will ignore
        return {"schemaId": self.schema_id, **self.to_mal_ndjson()}


class Dropdown(BaseModel):
    answer: List[ClassificationAnswer]

    def to_mal_ndjson(self):
        raise NotImplementedError(
            "MAL Does not support the dropdown tool at this time")

    def to_mal_subclass_ndjson(self):
        self.to_mal_ndjson()


class Classification:
    value: Union[Dropdown, Text, CheckList, Radio]

class Subclass(Classification, FeatureSchemaRef):
    classifications: List["Subclass"] = []
# To support recursive subclasses
Subclass.update_forward_refs()
