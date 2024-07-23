from typing import Dict


def _check_keys(key: str) -> bool:
    if "customMetrics" == key:
        return True
    if "custom_metrics" == key:
        return True
    if "keyframe" == key:
        return True
    if "classifications" == key:
        return True
    if "confidence" == key:
        return True
    if "name" == key:
        return True
    if 'featureSchemaId' == key:
        return True
    if "schemaId" == key:
        return True
    return False
    
def _feature_serializer(res: Dict) -> Dict:
    """Used with custom model serializer for Pydantics. This ensures backwards compatibility since Pydantic V1 allowed you to override dict/model_dump method that worked with nested models. This method needs to be used for all base classes and sub classes for same behavior with a model_serializer decorator. We should look at getting this removed by allowing our API to accept null values for fields that are optional."""
    for k, v in res.items():
        if _check_keys(k) and v == None:
            del res[k]
        if isinstance(res[k], Dict):
            _feature_serializer(v)
    return res
    