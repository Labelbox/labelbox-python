import abc
from dataclasses import dataclass

from typing import Any, Callable, Dict, List, Optional, Union

from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.utils import snake_case, camel_case


@dataclass
class OntologyEntity:
    required: bool
    name: str


@dataclass
class Option:
    label: str
    value: str
    feature_schema_id: Optional[str] = None
    schema_node_id: Optional[str] = None

    @classmethod
    def from_json(cls, json_dict):
        _dict = convert_keys(json_dict, snake_case)
        return cls(**_dict)


@dataclass
class Classification(OntologyEntity):
    type: str
    instructions: str
    options: List[Option]
    feature_schema_id: Optional[str] = None
    schema_node_id: Optional[str] = None

    @classmethod
    def from_json(cls, json_dict):
        _dict = convert_keys(json_dict, snake_case)
        _dict['options'] = [
            Option.from_json(option) for option in _dict['options']
        ]
        return cls(**_dict)


@dataclass
class Tool(OntologyEntity):
    tool: str
    color: str
    classifications: List[Classification]
    feature_schema_id: Optional[str] = None
    schema_node_id: Optional[str] = None

    @classmethod
    def from_json(cls, json_dict):
        _dict = convert_keys(json_dict, snake_case)
        _dict['classifications'] = [
            Classification.from_json(classification)
            for classification in _dict['classifications']
        ]
        return cls(**_dict)


"""
* The reason that an ontology is read only is because it is a second class citizen to labeling front end options.
** This is because it is a more specific implementation of this.

- However, we want to support ontologies as if they were labeling front ends.
- With this special relationship we can override the default behavior to mock the appropriate changes to the labeling front end


###Note: The only problem is that you can't just create a stand alone ontology. right? 
# - Since you need to create a project and query the project ontology before one exists.

^^^^^^^ This is the worst. Even with hackery, you can't force a DB entry without create a new proj :(
     However, labeling front-ends cannot be created without projects either! So maybe we just copy the use cases of that.
     Use this as the simpler interface and make it clear that this is just a limited version

"""


class OntologyRelationship(Relationship):

    def __get__(self, parent):
        if not self.parent:
            self.parent = parent
        return self

    def __init__(self):
        super(OntologyRelationship, self).__init__()
        self.parent = None

    def __call__(self):
        if self.parent.setup_complete is None:
            #As it currently stands, it creates a new ontology with no new tools and the ontology cannot be edited.
            return None
        return super().__call__

    def connect(self, other_ontology):
        if not isinstance(other_ontology, OntologyRelationship):
            raise Exception("only support ")

    def disconnect(self):
        raise Exception(
            "Disconnect is not supported for Onotlogy. Instead connect another ontology to replace the current one."
        )


class Ontology(DbObject):
    """An ontology specifies which tools and classifications are available
    to a project. This is read only for now.

    Attributes:
        name (str)
        description (str)
        updated_at (datetime)
        created_at (datetime)
        normalized (json)
        object_schema_count (int)
        classification_schema_count (int)

        projects (Relationship): `ToMany` relationship to Project
        created_by (Relationship): `ToOne` relationship to User
    """

    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    normalized = Field.Json("normalized")
    object_schema_count = Field.Int("object_schema_count")
    classification_schema_count = Field.Int("classification_schema_count")

    projects = Relationship.ToMany("Project", True)
    created_by = Relationship.ToOne("User", False, "created_by")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tools: Optional[List[Tool]] = None
        self._classifications: Optional[List[Classification]] = None

    def tools(self) -> List[Tool]:
        """Get list of tools (AKA objects) in an Ontology."""
        if self._tools is None:
            self._tools = [
                Tool.from_json(tool) for tool in self.normalized['tools']
            ]
        return self._tools  # type: ignore

    def classifications(self) -> List[Classification]:
        """Get list of classifications in an Ontology."""
        if self._classifications is None:
            self._classifications = [
                Classification.from_json(classification)
                for classification in self.normalized['classifications']
            ]
        return self._classifications  # type: ignore


def convert_keys(json_dict: Dict[str, Any],
                 converter: Callable) -> Dict[str, Any]:
    if isinstance(json_dict, dict):
        return {
            converter(key): convert_keys(value, converter)
            for key, value in json_dict.items()
        }
    if isinstance(json_dict, list):
        return [convert_keys(ele, converter) for ele in json_dict]
    return json_dict
