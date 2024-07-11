import pytest

from labelbox import ProjectRole
from faker import Faker

faker = Faker()

def test_org_invite(client, organization, environ, queries):
    role = client.get_roles()['LABELER']
    dummy_email = "none+{}@labelbox.com".format("".join(faker.random_letters(26)))
    invite_limit = organization.invite_limit()

    if environ.value == "prod":
        assert invite_limit.remaining > 0, "No invites available for the account associated with this key."
    elif environ.value != "staging":
        # Cannot run against local
        return

    invite = organization.invite_user(dummy_email, role)

    if environ.value == "prod":

        invite_limit_after = organization.invite_limit()
        # One user added
        assert invite_limit.remaining - invite_limit_after.remaining == 1
        # An invite shouldn't effect the user count until after it is accepted

    outstanding_invites = queries.get_invites(client)
    in_list = False

    for invite in outstanding_invites:
        if invite.uid == invite.uid:
            in_list = True
            org_role = invite.organization_role_name.lower()
            assert org_role == role.name.lower(
            ), "Role should be labeler. Found {org_role} "
    assert in_list, "Invite not found"
    queries.cancel_invite(client, invite.uid)
    assert invite_limit.remaining - organization.invite_limit().remaining == 0


def test_project_invite(client, organization, project_pack, queries):
    project_1, project_2 = project_pack
    roles = client.get_roles()
    dummy_email = "none+{}@labelbox.com".format("".join(faker.random_letters(26)))
    project_role_1 = ProjectRole(project=project_1, role=roles['LABELER'])
    project_role_2 = ProjectRole(project=project_2, role=roles['REVIEWER'])
    invite = organization.invite_user(
        dummy_email,
        roles['NONE'],
        project_roles=[project_role_1, project_role_2])

    project_invite = next(queries.get_project_invites(client, project_1.uid))

    assert set([(proj_invite.project.uid, proj_invite.role.uid)
                for proj_invite in project_invite.project_roles
               ]) == set([(proj_role.project.uid, proj_role.role.uid)
                          for proj_role in [project_role_1, project_role_2]])

    assert set([(proj_invite.project.uid, proj_invite.role.uid)
                for proj_invite in project_invite.project_roles
               ]) == set([(proj_role.project.uid, proj_role.role.uid)
                          for proj_role in [project_role_1, project_role_2]])

    project_members = project_1.members()

    project_member = [
        member for member in project_members
        if member.user().uid == client.get_user().uid
    ]

    assert len(project_member) == 1
    project_member = project_member[0]

    assert project_member.access_from == 'ORGANIZATION'
    assert project_member.role().name.upper() == roles['ADMIN'].name.upper()
    queries.cancel_invite(client, invite.uid)


@pytest.mark.skip(
    "Unable to programatically create user without accepting an email invite. Add back once there is a workaround."
)
def test_member_management(client, organization, project, project_based_user):
    roles = client.get_roles()
    assert not len(list(project_based_user.projects()))
    for role in [roles['LABELER'], roles['REVIEWER']]:

        project_based_user.upsert_project_role(project, role=role)
        members = project.members()
        is_member = False
        for member in members:
            if member.user().uid == project_based_user.uid:
                is_member = True
                assert member.role().name.upper() == role.name.upper()
                break
        assert is_member

    project_based_user.remove_from_project(project)
    is_member = False
    for member in project.members():
        assert member.user().uid != project_based_user.uid

    assert project_based_user.org_role().name.upper(
    ) == roles['NONE'].name.upper()
    for role in [
            roles['TEAM_MANAGER'], roles['ADMIN'], roles['LABELER'],
            roles['REVIEWER']
    ]:
        project_based_user.update_org_role(role)
        project_based_user.org_role().name.upper() == role.name.upper()

    organization.remove_user(project_based_user)
    for user in organization.users():
        assert project_based_user.uid != user.uid
