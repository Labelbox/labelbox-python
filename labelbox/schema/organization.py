from typing import List
from labelbox.orm.query import update_fields
from labelbox.pagination import PaginatedCollection
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.schema.user import Invitee, ProjectRole, User




class Organization(DbObject):
    """ An Organization is a group of Users.

    It is associated with data created by Users within that Organization.
    Typically all Users within an Organization have access to data created by any User in the same Organization.

    Attributes:
        updated_at (datetime)
        created_at (datetime)
        name (str)

        users (Relationship): `ToMany` relationship to User
        projects (Relationship): `ToMany` relationship to Project
        webhooks (Relationship): `ToMany` relationship to Webhook
    """

    # RelationshipManagers in Organization use the type in Query (and
    # not the source object) because the server-side does not support
    # filtering on ID in the query for getting a single organization.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for relationship in self.relationships():
            getattr(self, relationship.name).filter_on_id = False

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")

    # Relationships
    users = Relationship.ToMany("User", False)
    projects = Relationship.ToMany("Project", True)
    webhooks = Relationship.ToMany("Webhook", False)


    def get_user_invites(self):
        query_str = """query GetOrgInvitations($from: ID, $first: PageSize) {
                organization {
                    id
                    invites(from: $from, first: $first) {
                        nodes {
                            id
                            createdAt
                            organizationRoleName
                            inviteeEmail
                        }
                        nextCursor
                    }
                }
            }"""
        
        return PaginatedCollection(self.client, query_str, {}, ['organization','invites','nodes'], Invitee, cursor_path = ['organization','invites','nextCursor'], experimental= True)

    def invite_user(self, email, role ,  projects : List[ProjectRole] = []):   
        # TODO: Understand edge cases. Catch limit exception.. 
        # Also the expected upsert behavior doesn't seem to be happening. 
        query_str = """mutation createInvites($data: [CreateInviteInput!]){
                    createInvites(data: $data){
                        invite {
                            id
                        }
                    }
                }"""

        return self.client.execute(query_str,{'data' : [{
                            "inviterId"  : self.client.get_user().uid,
                            "inviteeEmail" : email,
                            "organizationId" : self.uid,
                            "organizationRoleId" :  role,
                            "projects" : projects
                }]}, experimental= True)


    def cancel_invite(self, invite_id): 
        # TODO: Give a way for user to get invite_id from email..
        query_str = """mutation CancelInvite($where: WhereUniqueIdInput!) {
            cancelInvite(where: $where) {
                id
            }
        }"""
        return self.client.execute(query_str, {'where' : {'id' : invite_id}}, experimental= True)


    def user_limit(self):
        # Org is based off of the user credentials, so no args
        query_str = """
            query UsersLimit {
            organization {
                id
                account {
                id
                usersLimit {
                    dateLimitWasReached
                    remaining
                    used
                    limit   
                }
                
                }
            }
        }
        """
        res = self.client.execute(query_str, experimental= True)
        return res['organization']['account']['usersLimit'] # {'dateLimitWasReached': None, 'remaining': 1, 'used': 2, 'limit': 3}

        
    def restore_users(self, user):
        query_string, params = update_fields(user, {User.deleted : False})
        res = self.client.execute(query_string, params)
        return res

    def get_deleted_user(self, email):
        return  next(self.users(where = ( (User.email == email) & ( User.deleted == True)) ), None)
        
    def remove_from_org(user):
        # might just be able to do user.delete()
        # or user.update({'deleted' : True})
        """mutation DeleteMember($id: ID!) {
            updateUser(where: {id: $id}, data: {deleted: true}) {
            id
            deleted
    
            }
        }"""
