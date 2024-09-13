from typing import Any, Dict, List, Set


class LabelsConfidencePresenceChecker:
    """
    Checks if a given list of labels contains at least one confidence score
    """

    @classmethod
    def check(cls, raw_labels: List[Dict[str, Any]]):
        keys: Set[str] = set([])
        cls._collect_keys_from_list(raw_labels, keys)
        return len(keys.intersection(set(["confidence"]))) == 1

    @classmethod
    def _collect_keys_from_list(
        cls, objects: List[Dict[str, Any]], keys: Set[str]
    ):
        for obj in objects:
            if isinstance(obj, (list, tuple)):
                cls._collect_keys_from_list(obj, keys)
            elif isinstance(obj, dict):
                cls._collect_keys_from_object(obj, keys)

    @classmethod
    def _collect_keys_from_object(cls, object: Dict[str, Any], keys: Set[str]):
        for key in object:
            keys.add(key)
            if isinstance(object[key], dict):
                cls._collect_keys_from_object(object[key], keys)
            if isinstance(object[key], (list, tuple)):
                cls._collect_keys_from_list(object[key], keys)
