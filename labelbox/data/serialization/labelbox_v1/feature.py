from pydantic import BaseModel


class LBV1Feature(BaseModel):
    featureId: str
    schemaId: str
    title: str
    value: str
