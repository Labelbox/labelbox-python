from typing import Optional


def pydantic_import(class_name, sub_module_path: Optional[str] = None):
    import importlib
    import importlib.metadata

    # Get the version of pydantic
    pydantic_version = importlib.metadata.version("pydantic")

    # Determine the module name based on the version
    module_name = "pydantic" if pydantic_version.startswith(
        "1") else "pydantic.v1"
    module_name = f"{module_name}.{sub_module_path}" if sub_module_path else module_name

    # Import the class from the module
    klass = getattr(importlib.import_module(module_name), class_name)

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
