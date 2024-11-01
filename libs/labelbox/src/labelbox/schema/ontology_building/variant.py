from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class Variant:
    """
    A variant is a single option in step-by-step reasoning or fact-checking tool.
    """

    id: int
    name: str

    def asdict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name}


@dataclass
class VariantWithActions(Variant):
    actions: List[str] = field(default_factory=list)
    _available_actions: Set[str] = field(default_factory=set)

    def set_actions(self, actions: List[str]) -> None:
        self.actions = []
        for action in actions:
            if action in self._available_actions:
                self.actions.append(action)

    def reset_actions(self) -> None:
        self.actions = []

    def asdict(self) -> Dict[str, Any]:
        data = super().asdict()
        data["actions"] = self.actions

        return data
