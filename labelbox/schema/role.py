from dataclasses import dataclass
from typing import Dict, Optional, TYPE_CHECKING

from labelbox.orm.model import Field
from labelbox.orm.db_object import DbObject
from labelbox.schema.project import Project

if TYPE_CHECKING:
    from labelbox import Client

_ROLES: Optional[Dict[str, "Role"]] = None


def get_roles(client: "Client") -> Dict[str, "Role"]:
    global _ROLES
    if _ROLES is None:
        query_str = """query GetAvailableUserRolesPyApi { roles { id name } }"""
        res = client.execute(query_str)
        _ROLES = {}
        for role in res['roles']:
            role['name'] = format_role(role['name'])
            _ROLES[role['name']] = Role(client, role)
    return _ROLES


def format_role(name: str):
    return name.upper().replace(' ', '_')


class Role(DbObject):
    name = Field.String("name")


class OrgRole(Role):
    ...


class UserRole(Role):
    ...


@dataclass
class ProjectRole:
    project: Project
    role: Role
