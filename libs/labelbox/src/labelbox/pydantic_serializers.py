from typing import Dict

def _feature_serializer(res: Dict) -> Dict:
    """Used as a with custom model serializer for pydantics. This ensures backwards compatibility since pydantic V1 allowed you to override Dict method. This method needs to be used for all base classes and sub classes. We should look at getting this removed."""
    if "customMetrics" in res and res["customMetrics"] is None:
        res.pop("customMetrics")
    if "custom_metrics" in res and res["custom_metrics"] is None:
        res.pop("custom_metrics")
    if "keyframe" in res and res["keyframe"] == None:
        res.pop("keyframe")
    if "classifications" in res and res["classifications"] == []:
        res.pop("classifications")
    if "confidence" in res and res["confidence"] is None:
        res.pop("confidence")
    if 'name' in res and res['name'] is None:
        res.pop('name')
    if 'featureSchemaId' in res and res['featureSchemaId'] is None:
        res.pop('featureSchemaId')
    
    return res
    