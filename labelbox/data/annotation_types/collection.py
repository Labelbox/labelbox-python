



from labelbox.data.annotation_types.annotation import Annotation
from typing import Dict, List

class AnnotationCollection:
    # it needs to upload to data rows if that doesn't exist....
    data : List[Annotation]
    _data_dict : Dict[data_row_id : List[Annotation]]


    def create_dataset














