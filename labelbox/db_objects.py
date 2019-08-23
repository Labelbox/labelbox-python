from enum import Enum

from labelbox.query import Field, DbObject

""" Defines client-side objects representing database content. """


class Project(DbObject):
    uid = Field("uid", "id")
    name = Field("name")
    description = Field("description")
    updated_at = Field("updated_at")
    created_at = Field("created_at")
