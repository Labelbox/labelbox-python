# type: ignore

import colorsys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Type
from typing_extensions import Annotated
import warnings

from labelbox.exceptions import InconsistentOntologyException
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
import json
from pydantic import StringConstraints

FeatureSchemaId: Type[str] = Annotated[
    str, StringConstraints(min_length=25, max_length=25)
]
SchemaId: Type[str] = Annotated[
    str, StringConstraints(min_length=25, max_length=25)
]


class DeleteFeatureFromOntologyResult:
    archived: bool
    deleted: bool

    def __str__(self):
        return "<%s %s>" % (
            self.__class__.__name__.split(".")[-1],
            json.dumps(self.__dict__),
        )


class FeatureSchema(DbObject):
    name = Field.String("name")
    color = Field.String("name")
    normalized = Field.Json("normalized")


@dataclass
class Option:
    """
    An option is a possible answer within a Classification object in
    a Project's ontology.

    To instantiate, only the "value" parameter needs to be passed in.

    Example(s):
        option = Option(value = "Option Example")

    Attributes:
        value: (str)
        schema_id: (str)
        feature_schema_id: (str)
        options: (list)
    """

    value: Union[str, int]
    label: Optional[Union[str, int]] = None
    schema_id: Optional[str] = None
    feature_schema_id: Optional[FeatureSchemaId] = None
    options: Union[
        List["Classification"], List["PromptResponseClassification"]
    ] = field(default_factory=list)

    def __post_init__(self):
        if self.label is None:
            self.label = self.value

    @classmethod
    def from_dict(
        cls, dictionary: Dict[str, Any]
    ) -> Dict[Union[str, int], Union[str, int]]:
        return cls(
            value=dictionary["value"],
            label=dictionary["label"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            options=[
                Classification.from_dict(o)
                for o in dictionary.get("options", [])
            ],
        )

    def asdict(self) -> Dict[str, Any]:
        return {
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "label": self.label,
            "value": self.value,
            "options": [o.asdict(is_subclass=True) for o in self.options],
        }

    def add_option(
        self, option: Union["Classification", "PromptResponseClassification"]
    ) -> None:
        if option.name in (o.name for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate nested classification '{option.name}' "
                f"for option '{self.label}'"
            )
        self.options.append(option)


@dataclass
class Classification:
    """
    A classification to be added to a Project's ontology. The
    classification is dependent on the Classification Type.

    To instantiate, the "class_type" and "name" parameters must
    be passed in.

    The "options" parameter holds a list of Option objects. This is not
    necessary for some Classification types, such as TEXT. To see which
    types require options, look at the "_REQUIRES_OPTIONS" class variable.

    Example(s):
        classification = Classification(
            class_type = Classification.Type.TEXT,
            name = "Classification Example")

        classification_two = Classification(
            class_type = Classification.Type.RADIO,
            name = "Second Example")
        classification_two.add_option(Option(
            value = "Option Example"))

    Attributes:
        class_type: (Classification.Type)
        name: (str)
        instructions: (str)
        required: (bool)
        options: (list)
        ui_mode: (str)
        schema_id: (str)
        feature_schema_id: (str)
        scope: (str)
    """

    class Type(Enum):
        TEXT = "text"
        CHECKLIST = "checklist"
        RADIO = "radio"

    class Scope(Enum):
        GLOBAL = "global"
        INDEX = "index"

    class UIMode(Enum):
        HOTKEY = "hotkey"
        SEARCHABLE = "searchable"

    _REQUIRES_OPTIONS = {Type.CHECKLIST, Type.RADIO}

    class_type: Type
    name: Optional[str] = None
    instructions: Optional[str] = None
    required: bool = False
    options: List[Option] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    scope: Scope = None
    ui_mode: Optional[UIMode] = (
        None  # How this classification should be answered (e.g. hotkeys / autocomplete, etc)
    )

    def __post_init__(self):
        if self.name is None:
            msg = (
                "When creating the Classification feature, please use “name” "
                "for the classification schema name, which will be used when "
                "creating annotation payload for Model-Assisted Labeling "
                "Import and Label Import. “instructions” is no longer "
                "supported to specify classification schema name."
            )
            if self.instructions is not None:
                self.name = self.instructions
                warnings.warn(msg)
            else:
                raise ValueError(msg)
        else:
            if self.instructions is None:
                self.instructions = self.name

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        return cls(
            class_type=cls.Type(dictionary["type"]),
            name=dictionary["name"],
            instructions=dictionary["instructions"],
            required=dictionary.get("required", False),
            options=[Option.from_dict(o) for o in dictionary["options"]],
            ui_mode=cls.UIMode(dictionary["uiMode"])
            if "uiMode" in dictionary
            else None,
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            scope=cls.Scope(dictionary.get("scope", cls.Scope.GLOBAL)),
        )

    def asdict(self, is_subclass: bool = False) -> Dict[str, Any]:
        if self.class_type in self._REQUIRES_OPTIONS and len(self.options) < 1:
            raise InconsistentOntologyException(
                f"Classification '{self.name}' requires options."
            )
        classification = {
            "type": self.class_type.value,
            "instructions": self.instructions,
            "name": self.name,
            "required": self.required,
            "options": [o.asdict() for o in self.options],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
        }
        if (
            self.class_type == self.Type.RADIO
            or self.class_type == self.Type.CHECKLIST
        ) and self.ui_mode:
            # added because this key does nothing for text so no point of including
            classification["uiMode"] = self.ui_mode.value
        if is_subclass:
            return classification
        classification["scope"] = (
            self.scope.value
            if self.scope is not None
            else self.Scope.GLOBAL.value
        )
        return classification

    def add_option(self, option: Option) -> None:
        if option.value in (o.value for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate option '{option.value}' "
                f"for classification '{self.name}'."
            )
        self.options.append(option)


@dataclass
class ResponseOption(Option):
    """
    An option is a possible answer within a PromptResponseClassification response object in
    a Project's ontology.

    To instantiate, only the "value" parameter needs to be passed in.

    Example(s):
        option = ResponseOption(value = "Response Option Example")

    Attributes:
        value: (str)
        schema_id: (str)
        feature_schema_id: (str)
        options: (list)
    """

    @classmethod
    def from_dict(
        cls, dictionary: Dict[str, Any]
    ) -> Dict[Union[str, int], Union[str, int]]:
        return cls(
            value=dictionary["value"],
            label=dictionary["label"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            options=[
                PromptResponseClassification.from_dict(o)
                for o in dictionary.get("options", [])
            ],
        )


@dataclass
class PromptResponseClassification:
    """

    A PromptResponseClassification to be added to a Project's ontology. The
    classification is dependent on the PromptResponseClassification Type.

    To instantiate, the "class_type" and "name" parameters must
    be passed in.

    The "options" parameter holds a list of Response Option objects. This is not
    necessary for some Classification types, such as RESPONSE_TEXT or PROMPT. To see which
    types require options, look at the "_REQUIRES_OPTIONS" class variable.

    Example(s):
    >>>    classification = PromptResponseClassification(
    >>>        class_type = PromptResponseClassification.Type.Prompt,
    >>>        character_min = 1,
    >>>        character_max = 1
    >>>        name = "Prompt Classification Example")

    >>>    classification_two = PromptResponseClassification(
    >>>        class_type = PromptResponseClassification.Type.RESPONSE_RADIO,
    >>>        name = "Second Example")

    >>>    classification_two.add_option(ResponseOption(
    >>>        value = "Option Example"))

    Attributes:
        class_type: (Classification.Type)
        name: (str)
        instructions: (str)
        required: (bool)
        options: (list)
        character_min: (int)
        character_max: (int)
        schema_id: (str)
        feature_schema_id: (str)
    """

    def __post_init__(self):
        if self.name is None:
            msg = (
                "When creating the Classification feature, please use “name” "
                "for the classification schema name, which will be used when "
                "creating annotation payload for Model-Assisted Labeling "
                "Import and Label Import. “instructions” is no longer "
                "supported to specify classification schema name."
            )
            if self.instructions is not None:
                self.name = self.instructions
                warnings.warn(msg)
            else:
                raise ValueError(msg)
        else:
            if self.instructions is None:
                self.instructions = self.name

    class Type(Enum):
        PROMPT = "prompt"
        RESPONSE_TEXT = "response-text"
        RESPONSE_CHECKLIST = "response-checklist"
        RESPONSE_RADIO = "response-radio"

    _REQUIRES_OPTIONS = {Type.RESPONSE_CHECKLIST, Type.RESPONSE_RADIO}

    class_type: Type
    name: Optional[str] = None
    instructions: Optional[str] = None
    required: bool = True
    options: List[ResponseOption] = field(default_factory=list)
    character_min: Optional[int] = None
    character_max: Optional[int] = None
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        return cls(
            class_type=cls.Type(dictionary["type"]),
            name=dictionary["name"],
            instructions=dictionary["instructions"],
            required=True,  # always required
            options=[
                ResponseOption.from_dict(o) for o in dictionary["options"]
            ],
            character_min=dictionary.get("minCharacters", None),
            character_max=dictionary.get("maxCharacters", None),
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
        )

    def asdict(self, is_subclass: bool = False) -> Dict[str, Any]:
        if self.class_type in self._REQUIRES_OPTIONS and len(self.options) < 1:
            raise InconsistentOntologyException(
                f"Response Classification '{self.name}' requires options."
            )
        classification = {
            "type": self.class_type.value,
            "instructions": self.instructions,
            "name": self.name,
            "required": True,  # always required
            "options": [o.asdict() for o in self.options],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
        }
        if (
            self.class_type == self.Type.PROMPT
            or self.class_type == self.Type.RESPONSE_TEXT
        ):
            if self.character_min:
                classification["minCharacters"] = self.character_min
            if self.character_max:
                classification["maxCharacters"] = self.character_max
        if is_subclass:
            return classification
        return classification

    def add_option(self, option: ResponseOption) -> None:
        if option.value in (o.value for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate option '{option.value}' "
                f"for response classification '{self.name}'."
            )
        self.options.append(option)


@dataclass
class Tool:
    """
    A tool to be added to a Project's ontology. The tool is
    dependent on the Tool Type.

    To instantiate, the "tool" and "name" parameters must
    be passed in.

    The "classifications" parameter holds a list of Classification objects.
    This can be used to add nested classifications to a tool.

    Example(s):
        tool = Tool(
            tool = Tool.Type.LINE,
            name = "Tool example")
        classification = Classification(
            class_type = Classification.Type.TEXT,
            instructions = "Classification Example")
        tool.add_classification(classification)

    Attributes:
        tool: (Tool.Type)
        name: (str)
        required: (bool)
        color: (str)
        classifications: (list)
        schema_id: (str)
        feature_schema_id: (str)
    """

    class Type(Enum):
        POLYGON = "polygon"
        SEGMENTATION = "superpixel"
        RASTER_SEGMENTATION = "raster-segmentation"
        POINT = "point"
        BBOX = "rectangle"
        LINE = "line"
        NER = "named-entity"
        RELATIONSHIP = "edge"
        MESSAGE_SINGLE_SELECTION = "message-single-selection"
        MESSAGE_MULTI_SELECTION = "message-multi-selection"
        MESSAGE_RANKING = "message-ranking"

    tool: Type
    name: str
    required: bool = False
    color: Optional[str] = None
    classifications: List[Classification] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        return cls(
            name=dictionary["name"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            required=dictionary.get("required", False),
            tool=cls.Type(dictionary["tool"]),
            classifications=[
                Classification.from_dict(c)
                for c in dictionary["classifications"]
            ],
            color=dictionary["color"],
        )

    def asdict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool.value,
            "name": self.name,
            "required": self.required,
            "color": self.color,
            "classifications": [
                c.asdict(is_subclass=True) for c in self.classifications
            ],
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
        }

    def add_classification(self, classification: Classification) -> None:
        if classification.name in (c.name for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate nested classification '{classification.name}' "
                f"for tool '{self.name}'"
            )
        self.classifications.append(classification)


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
        self._classifications: Optional[
            Union[List[Classification], List[PromptResponseClassification]]
        ] = None

    def tools(self) -> List[Tool]:
        """Get list of tools (AKA objects) in an Ontology."""
        if self._tools is None:
            self._tools = [
                Tool.from_dict(tool) for tool in self.normalized["tools"]
            ]
        return self._tools

    def classifications(
        self,
    ) -> List[Union[Classification, PromptResponseClassification]]:
        """Get list of classifications in an Ontology."""
        if self._classifications is None:
            self._classifications = []
            for classification in self.normalized["classifications"]:
                if (
                    "type" in classification
                    and classification["type"]
                    in PromptResponseClassification.Type._value2member_map_.keys()
                ):
                    self._classifications.append(
                        PromptResponseClassification.from_dict(classification)
                    )
                else:
                    self._classifications.append(
                        Classification.from_dict(classification)
                    )
        return self._classifications


@dataclass
class OntologyBuilder:
    """
    A class to help create an ontology for a Project. This should be used
    for making Project ontologies from scratch. OntologyBuilder can also
    pull from an already existing Project's ontology.

    There are no required instantiation arguments.

    To create an ontology, use the asdict() method after fully building your
    ontology within this class, and inserting it into project.setup() as the
    "labeling_frontend_options" parameter.

    Example:
        builder = OntologyBuilder()
        ...
        frontend = list(client.get_labeling_frontends())[0]
        project.setup(frontend, builder.asdict())

    attributes:
        tools: (list)
        classifications: (list)


    """

    tools: List[Tool] = field(default_factory=list)
    classifications: List[
        Union[Classification, PromptResponseClassification]
    ] = field(default_factory=list)

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> Dict[str, Any]:
        classifications = []
        for c in dictionary["classifications"]:
            if (
                "type" in c
                and c["type"]
                in PromptResponseClassification.Type._value2member_map_.keys()
            ):
                classifications.append(
                    PromptResponseClassification.from_dict(c)
                )
            else:
                classifications.append(Classification.from_dict(c))
        return cls(
            tools=[Tool.from_dict(t) for t in dictionary["tools"]],
            classifications=classifications,
        )

    def asdict(self) -> Dict[str, Any]:
        self._update_colors()
        classifications = []
        prompts = 0
        for c in self.classifications:
            if (
                hasattr(c, "class_type")
                and c.class_type in PromptResponseClassification.Type
            ):
                if c.class_type == PromptResponseClassification.Type.PROMPT:
                    prompts += 1
                    if prompts > 1:
                        raise ValueError(
                            "Only one prompt is allowed per ontology"
                        )
                classifications.append(PromptResponseClassification.asdict(c))
            else:
                classifications.append(Classification.asdict(c))
        return {
            "tools": [t.asdict() for t in self.tools],
            "classifications": classifications,
        }

    def _update_colors(self):
        num_tools = len(self.tools)

        for index in range(num_tools):
            hsv_color = (index * 1 / num_tools, 1, 1)
            rgb_color = tuple(
                int(255 * x) for x in colorsys.hsv_to_rgb(*hsv_color)
            )
            if self.tools[index].color is None:
                self.tools[index].color = "#%02x%02x%02x" % rgb_color

    @classmethod
    def from_project(cls, project: "project.Project") -> "OntologyBuilder":
        ontology = project.ontology().normalized
        return cls.from_dict(ontology)

    @classmethod
    def from_ontology(cls, ontology: Ontology) -> "OntologyBuilder":
        return cls.from_dict(ontology.normalized)

    def add_tool(self, tool: Tool) -> None:
        if tool.name in (t.name for t in self.tools):
            raise InconsistentOntologyException(
                f"Duplicate tool name '{tool.name}'. "
            )
        self.tools.append(tool)

    def add_classification(
        self,
        classification: Union[Classification, PromptResponseClassification],
    ) -> None:
        if classification.name in (c.name for c in self.classifications):
            raise InconsistentOntologyException(
                f"Duplicate classification name '{classification.name}'. "
            )
        self.classifications.append(classification)
