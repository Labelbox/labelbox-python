try:
    from labelbox.data.annotation_types import *
except ImportError:
    raise ImportError(
        "There are missing dependencies for `labelbox.types`, use `pip install labelbox[data] --upgrade` to install missing dependencies."
    )