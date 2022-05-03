from enum import Enum


class MediaType(Enum):
    """add DOCUMENT, GEOSPATIAL_TILE, SIMPLE_TILE to match the UI choices"""
    Audio = "AUDIO"
    Conversational = "CONVERSATIONAL"
    Dicom = "DICOM"
    Document = "PDF"
    Geospatial_Tile = "TMS_GEO"
    Image = "IMAGE"
    Json = "JSON"
    Pdf = "PDF"
    Simple_Tile = "TMS_SIMPLE"
    Text = "TEXT"
    Tms_Geo = "TMS_GEO"
    Tms_Simple = "TMS_SIMPLE"
    Video = "VIDEO"
    Unknown = "UNKNOWN"
    Unsupported = "UNSUPPORTED"

    @classmethod
    def _missing_(cls, name):
        """Handle missing null data types for projects 
            created without setting allowedMediaType
            Handle upper case names for compatibility with 
            the GraphQL"""

        if name is None:
            return cls.Unknown

        for member in cls.__members__:
            if member.name == name.upper():
                return member

    @classmethod
    def is_supported(cls, value):
        return isinstance(value,
                          cls) and value not in [cls.Unknown, cls.Unsupported]

    @classmethod
    def get_supported_members(cls):
        return [
            item for item in cls.__members__
            if item not in ["Unknown", "Unsupported"]
        ]
