
from labelbox.data.annotation_types.marshmallow import required
import marshmallow_dataclass
from marshmallow import ValidationError
from marshmallow.decorators import  validates_schema

@marshmallow_dataclass.dataclass
class TextEntity:
    start: int = required()
    end: int = required()

    @validates_schema
    def validate_start_end(self, data, **_) -> None:
        if (
            isinstance(data["location"].start, int)
            and isinstance(data["location"].end, int)
            and data["location"].start >= data["location"].end
        ):
            raise ValidationError("Location end must be greater or equal to start")

    def to_mal_ndjson(self):
        return {"location": {
            "start": self.start,
            "end": self.end
        }}


