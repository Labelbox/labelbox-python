from datetime import datetime
from labelbox.exceptions import LabelboxError, ResourceNotFoundError
from labelbox import utils
from typing import List, Optional
from labelbox.orm.query import update_fields
from labelbox.pagination import PaginatedCollection
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.schema.user import ProjectRole, User
from dataclasses import dataclass


@dataclass
class InviteLimit:
    remaining: int
    used: int
    limit: int


@dataclass
class UsersLimit(InviteLimit):
    date_limit_was_reached: Optional[datetime]


class Invitee(DbObject):
    created_at = Field.DateTime("created_at")
    organization_role_name = Field.String("organization_role_name")
    email = Field.String("email", "inviteeEmail")

    #projectInvites = ProjectInvitee

    def cancel(self):
        # TODO: Give a way for user to get invite_id from email..
        query_str = """mutation CancelInvite($where: WhereUniqueIdInput!) {
            cancelInvite(where: $where) {
                id
            }
        }"""
        self.client.execute(query_str, {'where': {
            'id': self.uid
        }},
                            experimental=True)


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
        return PaginatedCollection(
            self.client,
            query_str, {}, ['organization', 'invites', 'nodes'],
            Invitee,
            cursor_path=['organization', 'invites', 'nextCursor'],
            experimental=True)

    def invite_user(self, email, role, projects: List[ProjectRole] = []):
        remaining_invites = self.invite_limit().remaining
        if remaining_invites == 0:
            # Note that if the user already exists then we shouldn't throw this error...
            # Check if user exists
            # TODO: If they are deleted then what do we want to do?
            # Do we still check for number of seats? I guess so..
            if next(self.users((User.email == email) &
                               (User.deleted == True)), None) is None:
                raise LabelboxError(
                    "Invite(s) cannot be sent because you do not have enough available seats in your organization. "
                    "Please upgrade your account, revoke pending invitations or remove other users."
                )

        # TODO: Understand edge cases. Catch limit exception..
        # Also the expected upsert behavior doesn't seem to be happening.
        # If an invitation already exists for the user we have to revoke the current one
        # If the user already exists, then this will update permissions (maybe we can move the query to a new function)
        invites = self.get_user_invites()
        for invite in invites:
            if invite.email == email:
                raise ValueError(
                    f"Invite already exists for {email}. Please revoke the invite if you want to update the role or resend."
                )

        query_str = """mutation createInvites($data: [CreateInviteInput!]){
                    createInvites(data: $data){
                        invite {
                            id
                            createdAt
                            organizationRoleName
                            inviteeEmail
                        }
                    }
                }"""

        res = self.client.execute(query_str, {
            'data': [{
                "inviterId": self.client.get_user().uid,
                "inviteeEmail": email,
                "organizationId": self.uid,
                "organizationRoleId": role,
                "projects": projects
            }]
        },
                                   experimental=True) # We prob want to return an invitee
        return Invitee(self.client, res['invite'])

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
        res = self.client.execute(query_str, experimental=True)
        return UsersLimit(
            **{
                utils.snake_case(k): v for k, v in res['organization']
                ['account']['usersLimit'].items()
            })

    def invite_limit(self):
        # This accounts for users already in the org.
        # So used = users + invites, remaining = limit - (users + invites)
        #Try with different org to make sure this authenticates....
        res = self.client.execute("""query InvitesLimit($organizationId: ID!) {
            invitesLimit(where: {id: $organizationId}) {
                used
                limit
                remaining
            }
        }""", {"organizationId": self.uid},
                                  experimental=True)
        return InviteLimit(
            **{utils.snake_case(k): v for k, v in res['invitesLimit'].items()})

    # =====================
    # Not supporting for now..
    # =====================

    # Not sure how this works.. Especially when it makes you resend an email..
    def restore_users(self, user):
        query_string, params = update_fields(user, {User.deleted: False})
        res = self.client.execute(query_string, params)
        return res

    def get_deleted_user(self, email):
        return next(
            self.users(where=((User.email == email) & (User.deleted == True))),
            None)

    def remove_from_org(user):
        # might just be able to do user.delete()
        # or user.update({'deleted' : True})
        """mutation DeleteMember($id: ID!) {
            updateUser(where: {id: $id}, data: {deleted: true}) {
            id
            deleted
    
            }
        }"""


#create DbData class that all of the pydantic models inherit from. It will have its own constructor.
# Or just add in utils (apply_snake_to_dict)
