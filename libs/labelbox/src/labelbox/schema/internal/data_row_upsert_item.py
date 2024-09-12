from abc import ABC, abstractmethod

from typing import List, Tuple, Optional

from labelbox.schema.identifiable import UniqueId, GlobalKey
from labelbox.schema.data_row import DataRow
from pydantic import BaseModel


class DataRowItemBase(ABC, BaseModel):
    """
    Base class for creating payloads for upsert operations.
    """

    id: dict
    payload: dict

    @abstractmethod
    def is_empty(self) -> bool: ...

    @classmethod
    def build(
        cls,
        dataset_id: str,
        items: List[dict],
        key_types: Optional[Tuple[type, ...]] = (),
    ) -> List["DataRowItemBase"]:
        upload_items = []

        for item in items:
            # enforce current dataset's id for all specs
            item["dataset_id"] = dataset_id
            key = item.pop("key", None)
            if not key:
                key = {"type": "AUTO", "value": ""}
            elif isinstance(key, key_types):  # type: ignore
                key = {"type": key.id_type.value, "value": key.key}
            else:
                if not key_types:
                    raise ValueError(
                        f"Can not have a key for this item, got: {key}"
                    )
                raise ValueError(
                    f"Key must be an instance of {', '.join([t.__name__ for t in key_types])}, got: {type(item['key']).__name__}"
                )
            item = {
                k: v for k, v in item.items() if v is not None
            }  # remove None values
            upload_items.append(cls(payload=item, id=key))
        return upload_items


class DataRowUpsertItem(DataRowItemBase):
    def is_empty(self) -> bool:
        """
        The payload is considered empty if it's actually empty or the only key is `dataset_id`.
        :return: bool
        """
        return (
            not self.payload
            or len(self.payload.keys()) == 1
            and "dataset_id" in self.payload
        )

    @classmethod
    def build(
        cls,
        dataset_id: str,
        items: List[dict],
        key_types: Optional[Tuple[type, ...]] = (UniqueId, GlobalKey),
    ) -> List["DataRowItemBase"]:
        return super().build(dataset_id, items, (UniqueId, GlobalKey))


class DataRowCreateItem(DataRowItemBase):
    def is_empty(self) -> bool:
        """
        The payload is considered empty if it's actually empty or row_data is empty
            or the only key is `dataset_id`.
        :return: bool
        """
        row_data = self.payload.get("row_data", None) or self.payload.get(
            DataRow.row_data, None
        )

        return not self._is_legacy_conversational_data() and (
            not self.payload
            or len(self.payload.keys()) == 1
            and "dataset_id" in self.payload
            or row_data is None
            or len(row_data) == 0
        )

    def _is_legacy_conversational_data(self) -> bool:
        return (
            "conversationalData" in self.payload.keys()
            or "conversational_data" in self.payload.keys()
        )

    @classmethod
    def build(
        cls,
        dataset_id: str,
        items: List[dict],
        key_types: Optional[Tuple[type, ...]] = (),
    ) -> List["DataRowItemBase"]:
        return super().build(dataset_id, items, ())
