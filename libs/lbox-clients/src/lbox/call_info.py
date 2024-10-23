import inspect
import re
import sys
from typing import TypedDict


def python_version_info():
    version_info = sys.version_info

    return f"{version_info.major}.{version_info.minor}.{version_info.micro}-{version_info.releaselevel}"


LABELBOX_CALL_PATTERN = re.compile(r"/labelbox/")
TEST_FILE_PATTERN = re.compile(r".*test.*\.py$")


class _RequestInfo(TypedDict):
    prefix: str
    class_name: str
    method_name: str


def call_info():
    method_name: str = "Unknown"
    prefix = ""
    class_name = ""
    skip_methods = ["wrapper", "__init__", "execute"]
    skip_classes = ["PaginatedCollection", "_CursorPagination", "_OffsetPagination"]

    try:
        call_info = None
        for stack in reversed(inspect.stack()):
            if LABELBOX_CALL_PATTERN.search(stack.filename):
                call_info = stack
                method_name: str = call_info.function
                class_name = call_info.frame.f_locals.get(
                    "self", None
                ).__class__.__name__
                if method_name not in skip_methods:
                    if class_name not in skip_classes:
                        if TEST_FILE_PATTERN.search(call_info.filename):
                            prefix = "test:"
                        else:
                            if class_name == "NoneType":
                                class_name = ""
                            break

    except Exception:
        pass
    return _RequestInfo(prefix=prefix, class_name=class_name, method_name=method_name)


def call_info_as_str():
    info: _RequestInfo = call_info()
    return f"{info['prefix']}{info['class_name']}:{info['method_name']}"
