from typing import cast, Any, Dict, Generator, List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from labelbox.types import Label


def serialize_labels(
    objects: Union[List[Dict[str, Any]],
                   List["Label"]]) -> List[Dict[str, Any]]:
    """
    Checks if objects are of type Labels and serializes labels for annotation import. Serialization depends the labelbox[data] package, therefore NDJsonConverter is only loaded if using `Label` objects instead of `dict` objects.
    """
    if len(objects) == 0:
        return []

    is_label_type = not isinstance(objects[0], Dict)
    if is_label_type:
        # If a Label object exists, labelbox[data] is already installed, so no error checking is needed.
        from labelbox.data.serialization import NDJsonConverter
        labels = cast(List["Label"], objects)
        return list(NDJsonConverter.serialize(labels))

    return cast(List[Dict[str, Any]], objects)
