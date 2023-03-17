from pydantic import root_validator

from labelbox.utils import _CamelCaseMixin, is_exactly_one_set


class DataRow(_CamelCaseMixin):
    id: str = None
    global_key: str = None

    @root_validator()
    def must_set_one(cls, values):
        if not is_exactly_one_set(values.get('id'), values.get('global_key')):
            raise ValueError("Must set either id or global_key")
        return values
