from labelbox import Project, ExternalWorkforce
import os
import sys

def _get_workforce_id_for_test() -> str:
    # For this test, we need an additional organization id to connect the project to.
    # Given that the SDK is tested against multiple versions of Python, and different environments,
    # we decided to choose the organization id from 
    # https://labelbox.atlassian.net/wiki/spaces/PLT/pages/2110816271/How+to+labelbox-python+SDK+CI+Tests
    #
    # In particular, we have:
    # clum46jsb00jp07z338dh1gvb: for Python 3.8 in staging
    # cltp16p2v04dr07ywfgqxf23u: for Python 3.12 in staging    
    # ckcz6bubudyfi0855o1dt1g9s: for Python 3.8 in production
    # cltp1fral01dh07009zsng3zs: for Python 3.12 in production
    #
    # The idea is that when depending on the environment, if the current version of Python is 3.8,
    # then we use the organization id for Python 3.12. This way, We always us a different organization id
    # from the current one as an external workforce to avoid conflict.

    # Note: A better approach would be to create a new organization dynamically for testing purpose.
    # This is not currently possible.
    current_version = sys.version_info[:2]

    if os.environ['LABELBOX_TEST_ENVIRON'] == "staging":
        return "cltp16p2v04dr07ywfgqxf23u" if current_version == (3, 8) else "clum46jsb00jp07z338dh1gvb"
    else:
        return "cltp1fral01dh07009zsng3zs" if current_version == (3, 8) else "ckcz6bubudyfi0855o1dt1g9s"


def test_add_external_workforce(project: Project):
    workforce_id = _get_workforce_id_for_test()

    external_workforces = project.add_external_workforce(workforce_id)
    assert len(external_workforces) == 1
    assert isinstance(external_workforces[0], ExternalWorkforce)


def test_get_external_workforces(project: Project):
    workforce_id = _get_workforce_id_for_test()

    external_workforces = project.add_external_workforce(workforce_id)

    external_workforces = project.get_external_workforces()
    assert len(external_workforces) == 1
    assert isinstance(external_workforces[0], ExternalWorkforce)


def test_remove_external_workforce(project: Project):
    workforce_id = _get_workforce_id_for_test()
    external_workforces = project.add_external_workforce(workforce_id)

    external_workforces = project.remove_external_workforce(workforce_id)
    assert len(external_workforces) == 0


