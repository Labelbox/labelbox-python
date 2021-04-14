from dataclasses import dataclass

from labelbox.orm.model import Field
from labelbox.orm.db_object import DbObject
from labelbox.schema.project import Project


class Roles:
    """
    Object that manages org and user roles

        >>> roles = client.get_roles()
        >>> roles.valid_roles # lists all valid roles
        >>> roles['ADMIN'] # returns the admin Role

    """
    _instance = None

    def __new__(cls, client):
        if cls._instance is None:
            cls._instance = super(Roles, cls).__new__(cls)
            query_str = """query GetAvailableUserRolesPyApi { roles { id name } }"""
            res = client.execute(query_str)
            valid_roles = set()
            for result in res['roles']:
                _name = result['name'].upper().replace(' ', '_')
                result['name'] = _name
                setattr(cls._instance, _name, Role(client, result))
                valid_roles.add(_name)
            cls._instance.valid_roles = valid_roles
        cls._instance.index = 0
        return cls._instance

    def __repr__(self):
        return str({k: getattr(self, k) for k in self.valid_roles})

    def __getitem__(self, name):
        name = name.replace(' ', '_').upper()
        if name not in self.valid_roles:
            raise ValueError(
                f"No role named {name} exists. Valid names are one of {self.valid_roles}"
            )
        return getattr(self, name)

    def __iter__(self):
        self.key_iter = iter(self.valid_roles)
        return self

    def __next__(self):
        key = next(self.key_iter)
        return getattr(self, key)


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
