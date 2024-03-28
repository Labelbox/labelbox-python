from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class TaskQueue(DbObject):
    """
    a task queue

    Attributes
    name
    description
    queue_type
    data_row_count

    Relationships
    project
    organization
    pass_queue
    fail_queue
    """

    name = Field.String("name")
    description = Field.String("description")
    queue_type = Field.String("queue_type")
    data_row_count = Field.Int("data_row_count")

    def __init__(self, client, *args, **kwargs):
        super().__init__(client, *args, **kwargs)
