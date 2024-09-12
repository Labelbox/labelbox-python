from enum import Enum

from labelbox.utils import camel_case


class MediaType(Enum):
    Audio = "AUDIO"
    Conversational = "CONVERSATIONAL"
    Dicom = "DICOM"
    Document = "PDF"
    Geospatial_Tile = "TMS_GEO"
    Html = "HTML"
    Image = "IMAGE"
    LLMPromptCreation = "LLM_PROMPT_CREATION"
    LLMPromptResponseCreation = "LLM_PROMPT_RESPONSE_CREATION"
    Pdf = "PDF"
    Simple_Tile = "TMS_SIMPLE"
    Text = "TEXT"
    Tms_Geo = "TMS_GEO"
    Tms_Simple = "TMS_SIMPLE"
    Unknown = "UNKNOWN"
    Unsupported = "UNSUPPORTED"
    Video = "VIDEO"
    Point_Cloud = "POINT_CLOUD"
    LLM = "LLM"

    @classmethod
    def _missing_(cls, value):
        """Handle missing null data types for projects
        created without setting allowedMediaType
        Handle upper case names for compatibility with
        the GraphQL"""

        if value is None:
            return cls.Unknown

        def matches(value, name):
            """
            This will convert string values (from api) to match enum values
              Some string values come as snake case (i.e. llm-prompt-creation)
              Some string values come as camel case (i.e. llmPromptCreation)
                etc depending on which api returns the value
            """
            value_upper = value.upper()
            name_upper = name.upper()
            value_underscore = value.replace("-", "_")
            camel_case_value = camel_case(value_underscore)

            return (
                value_upper == name_upper
                or value_underscore.upper() == name_upper
                or camel_case_value.upper() == name_upper
            )

        for name, member in cls.__members__.items():
            if matches(value, name):
                return member

        return cls.Unsupported

    @classmethod
    def is_supported(cls, value):
        return isinstance(value, cls) and value not in [
            cls.Unknown,
            cls.Unsupported,
        ]

    @classmethod
    def get_supported_members(cls):
        return [
            item
            for item in cls.__members__
            if item not in ["Unknown", "Unsupported"]
        ]


def get_media_type_validation_error(media_type):
    return TypeError(
        f"{media_type} is not a valid media type. Use"
        f" any of {MediaType.get_supported_members()}"
        " from MediaType. Example: MediaType.Image."
    )
