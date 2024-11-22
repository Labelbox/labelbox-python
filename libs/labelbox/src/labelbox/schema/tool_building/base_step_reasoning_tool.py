import warnings
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from labelbox.schema.tool_building.tool_type import ToolType


@dataclass
class _Variant:
    id: int
    name: str
    actions: List[str] = field(default_factory=list)
    _available_actions: Set[str] = field(default_factory=set)

    def set_actions(self, actions: List[str]) -> None:
        self.actions = []
        for action in actions:
            if action in self._available_actions:
                self.actions.append(action)
            else:
                warnings.warn(
                    f"Variant ID {self.id} {action} is an invalid action, skipping"
                )

    def reset_actions(self) -> None:
        self.actions = []

    def asdict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "actions": self.actions,
        }

    def _post_init(self):
        # Call set_actions to remove any invalid actions
        self.set_actions(self.actions)


@dataclass
class _Definition:
    variants: List[_Variant]
    version: int = field(default=1)
    title: Optional[str] = None
    value: Optional[str] = None

    def __post_init__(self):
        if self.version != 1:
            raise ValueError("Invalid version")

    def asdict(self) -> Dict[str, Any]:
        result = {
            "variants": [variant.asdict() for variant in self.variants],
            "version": self.version,
        }
        if self.title is not None:
            result["title"] = self.title
        if self.value is not None:
            result["value"] = self.value
        return result

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "_Definition":
        variants = [_Variant(**variant) for variant in dictionary["variants"]]
        title = dictionary.get("title", None)
        value = dictionary.get("value", None)
        return cls(variants=variants, title=title, value=value)


@dataclass
class _BaseStepReasoningTool(ABC):
    name: str
    definition: _Definition
    type: Optional[ToolType] = None
    schema_id: Optional[str] = None
    feature_schema_id: Optional[str] = None
    color: Optional[str] = None
    required: bool = False  # This attribute is for consistency with other tools and backend, default is False

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Name is required")

    def asdict(self) -> Dict[str, Any]:
        return {
            "tool": self.type.value if self.type else None,
            "name": self.name,
            "required": self.required,
            "schemaNodeId": self.schema_id,
            "featureSchemaId": self.feature_schema_id,
            "definition": self.definition.asdict(),
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]) -> "_BaseStepReasoningTool":
        return cls(
            name=dictionary["name"],
            schema_id=dictionary.get("schemaNodeId", None),
            feature_schema_id=dictionary.get("featureSchemaId", None),
            required=dictionary.get("required", False),
            definition=_Definition.from_dict(dictionary["definition"]),
            color=dictionary.get("color", None),
        )
