import pytest

from labelbox.schema.organization import ProjectRole


def test_org_invite(client, organization, environ):
    role = client.get_roles()['LABELER']
    dummy_email = "none@labelbox.com"
    invite_limit = organization.invite_limit()

    if environ.value == "prod":
        user_limit = organization.user_limit()
        assert invite_limit.remaining > 0, "No invites available for the account associated with this key."
    elif environ.value != "staging":
        raise ValueError(
            f"Expected tests to run against either prod or staging. Found {environ}"
        )

    invite = organization.invite_user(dummy_email, role)

    if environ.value == "prod":
        invite_limit_after = organization.invite_limit()
        user_limit_after = organization.user_limit()
        # One user added
        assert invite_limit.remaining - invite_limit_after.remaining == 1
        # An invite shouldn't effect the user count until after it is accepted
        assert user_limit.remaining - user_limit_after.remaining == 0

    outstanding_invites = organization.invites()
    in_list = False
    for invite in outstanding_invites:
        if invite.uid == invite.uid:
            in_list = True
            org_role = invite.organization_role_name.lower()
            assert org_role == role.name.lower(
            ), "Role should be labeler. Found {org_role} "
    assert in_list, "Invite not found"

    with pytest.raises(ValueError) as exc_info:
        organization.invite_user(dummy_email, role)
    assert "Invite already exists for none@labelbox.com. Please revoke the invite if you want to update the role or resend." in str(
        exc_info.value)

    invite.revoke()
    assert invite_limit.remaining - organization.invite_limit().remaining == 0
    outstanding_invites = organization.invites()
    for invite in outstanding_invites:
        assert invite.uid != invite.uid, "Invite not deleted"


def check_empty_invites(project):
    assert next(project.invites(), None) is None


def test_project_invite(client, organization, project_pack):
    project_1, project_2 = project_pack
    roles = client.get_roles()
    dummy_email = "none1@labelbox.com"
    project_role_1 = ProjectRole(project_id=project_1.uid,
                                 project_role_id=roles['LABELER'].uid)
    project_role_2 = ProjectRole(project_id=project_2.uid,
                                 project_role_id=roles['REVIEWER'].uid)
    invite = organization.invite_user(
        dummy_email,
        roles['NONE'],
        project_roles=[project_role_1, project_role_2])

    project_invite = next(project_1.invites(), None)

    assert set([(proj_invite.project_id, proj_invite.project_role_id)
                for proj_invite in project_invite.project_roles
               ]) == set([(proj_role.project_id, proj_role.project_role_id)
                          for proj_role in [project_role_1, project_role_2]])

    assert set([(proj_invite.project_id, proj_invite.project_role_id)
                for proj_invite in project_invite.project_roles
               ]) == set([(proj_role.project_id, proj_role.project_role_id)
                          for proj_role in [project_role_1, project_role_2]])

    project_members = project_1.members()
    project_member = [
        member for member in project_members
        if member.user().uid == client.get_user().uid
    ]

    assert len(project_member) == 1
    project_member = project_member[0]

    assert project_member.role().name.upper() == roles['ADMIN'].name.upper()
    invite.revoke()


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
