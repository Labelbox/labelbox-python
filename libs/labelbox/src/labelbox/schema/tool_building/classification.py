import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from lbox.exceptions import InconsistentOntologyException

from labelbox.schema.tool_building.types import (
    FeatureSchemaId,
    FeatureSchemaAttributes,
    FeatureSchemaAttribute,
)


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
        attributes: (list)
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
    options: List["Option"] = field(default_factory=list)
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    scope: Optional[Scope] = None
    ui_mode: Optional[UIMode] = (
        None  # How this classification should be answered (e.g. hotkeys / autocomplete, etc)
    )
    attributes: Optional[FeatureSchemaAttributes] = None
    is_likert_scale: bool = False

    def __post_init__(self):
        if self.name is None:
            msg = (
                'When creating the Classification feature, please use "name" '
                "for the classification schema name, which will be used when "
                "creating annotation payload for Model-Assisted Labeling "
                'Import and Label Import. "instructions" is no longer '
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
        if self.attributes is not None:
            warnings.warn(
                "The attributes for Classifications are in beta. The attribute name and signature may change in the future."
            )

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "Classification":
        return cls(
            class_type=Classification.Type(dictionary["type"]),
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
            attributes=[
                FeatureSchemaAttribute.from_dict(attr)
                for attr in dictionary.get("attributes", []) or []
            ]
            if dictionary.get("attributes")
            else None,
            is_likert_scale=dictionary.get("isLikertScale", False),
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
            "attributes": [a.asdict() for a in self.attributes]
            if self.attributes is not None
            else None,
        }
        if self.class_type == self.Type.RADIO and self.is_likert_scale:
            # is_likert_scale is only applicable to RADIO classifications
            classification["isLikertScale"] = self.is_likert_scale
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

    def add_option(self, option: "Option") -> None:
        if option.value in (o.value for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate option '{option.value}' "
                f"for classification '{self.name}'."
            )
        # Auto-assign position if not set
        if option.position is None:
            option.position = len(self.options)
        self.options.append(option)


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
        position: (int) - Position of the option, auto-assigned starting from 0
    """

    value: Union[str, int]
    label: Optional[Union[str, int]] = None
    schema_id: Optional[str] = None
    feature_schema_id: Optional[FeatureSchemaId] = None  # type: ignore
    options: Union[
        List["Classification"], List["PromptResponseClassification"]
    ] = field(default_factory=list)
    position: Optional[int] = None

    def __post_init__(self):
        if self.label is None:
            self.label = self.value

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "Option":
        return cls(
            value=dictionary["value"],
            label=dictionary["label"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            options=[
                Classification.from_dict(o)
                for o in dictionary.get("options", [])
            ],
            position=dictionary.get("position", None),
        )

    def asdict(self) -> Dict[str, Any]:
        result = {
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "label": self.label,
            "value": self.value,
            "options": [o.asdict(is_subclass=True) for o in self.options],
        }
        if self.position is not None:
            result["position"] = self.position
        return result

    def add_option(
        self, option: Union["Classification", "PromptResponseClassification"]
    ) -> None:
        if option.name in (o.name for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate nested classification '{option.name}' "
                f"for option '{self.label}'"
            )
        self.options.append(option)  # type: ignore


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
                'When creating the Classification feature, please use "name" '
                "for the classification schema name, which will be used when "
                "creating annotation payload for Model-Assisted Labeling "
                'Import and Label Import. "instructions" is no longer '
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
    options: List["ResponseOption"] = field(default_factory=list)
    character_min: Optional[int] = None
    character_max: Optional[int] = None
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None

    @classmethod
    def from_dict(
        cls, dictionary: Dict[str, Any]
    ) -> "PromptResponseClassification":
        return cls(
            class_type=PromptResponseClassification.Type(dictionary["type"]),
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
        classification: Dict[str, Any] = {
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

    def add_option(self, option: "ResponseOption") -> None:
        if option.value in (o.value for o in self.options):
            raise InconsistentOntologyException(
                f"Duplicate option '{option.value}' "
                f"for response classification '{self.name}'."
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
    def from_dict(cls, dictionary: Dict[str, Any]) -> "ResponseOption":
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
