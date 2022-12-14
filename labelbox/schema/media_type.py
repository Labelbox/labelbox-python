from enum import Enum


class MediaType(Enum):
    Audio = "AUDIO"
    Conversational = "CONVERSATIONAL"
    Dicom = "DICOM"
    Document = "PDF"
    Geospatial_Tile = "TMS_GEO"
    Html = "HTML"
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


def get_media_type_validation_error(media_type):
    return TypeError(f"{media_type} is not a valid media type. Use"
                     f" any of {MediaType.get_supported_members()}"
                     " from MediaType. Example: MediaType.Image.")
