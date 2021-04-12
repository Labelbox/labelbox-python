from pydantic import BaseModel

from labelbox import utils
from labelbox.orm.model import Field
from labelbox.orm.db_object import DbObject


class Roles:
    """
    Object that manges org and user roles

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
        return str({k : getattr(self, k) for k in self.valid_roles})

    def __getitem__(self, name):
        if name in self.valid_roles:
            return getattr(self, name)
        else:
            raise ValueError(f"No role named {name} exists. Valid names are one of {self.valid_roles}")

    def __iter__(self):
        return self

    def __next__(self):
        try:
            key = self.valid_roles[self.index]
        except:
            raise StopIteration
        self.index += 1
        return getattr(self, key)



class Role(DbObject):
    name = Field.String("name")
  

class OrgRole(Role):
    ...

class UserRole(Role):
    ...


class ProjectRole(BaseModel):
    project_id: str
    project_role_id: str

    def dict(self):
        return {utils.camel_case(k) : v for k, v in super().dict().items()}



