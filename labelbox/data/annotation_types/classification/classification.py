from typing import List, Optional, Union

import marshmallow_dataclass
from labelbox.data.annotation_types.annotation import \
    Annotation
from labelbox.data.annotation_types.subclass import (
    CheckListFields, Classification, RadioFields, TextFields)



# TODO: Add a strict setting that checks names as set?
# How to deal with both schema ids and names... when there isn't a requirement to have a server side representation for annotation types?

