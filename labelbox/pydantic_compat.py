from typing import Optional


def pydantic_import(class_name, sub_module_path: Optional[str] = None):
    import importlib
    import pkg_resources

    # Get the version of pydantic
    pydantic_version = pkg_resources.get_distribution("pydantic").version

    # Check if the version is 1
    if pydantic_version.startswith("1"):
        pydantic_v1_module_name = "pydantic" if sub_module_path is None else f"pydantic.{sub_module_path}"
        klass = getattr(importlib.import_module("pydantic"), class_name)
    else:  # use pydantic 2 v1 thunk
        pydantic_v1_module_name = "pydantic.v1" if sub_module_path is None else f"pydantic.{sub_module_path}"

    klass = getattr(importlib.import_module(pydantic_v1_module_name),
                    class_name)

    return klass


BaseModel = pydantic_import("BaseModel")
PrivateAttr = pydantic_import("PrivateAttr")
Field = pydantic_import("Field")
ModelField = pydantic_import("ModelField", "fields")
ValidationError = pydantic_import("ValidationError")
ErrorWrapper = pydantic_import("ErrorWrapper", "error_wrappers")

validator = pydantic_import("validator")
root_validator = pydantic_import("root_validator")
conint = pydantic_import("conint")
conlist = pydantic_import("conlist")
constr = pydantic_import("constr")
confloat = pydantic_import("confloat")
