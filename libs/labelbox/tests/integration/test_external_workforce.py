from labelbox import Project, ExternalWorkforce
import os
import sys

def _get_workforce_id_for_test() -> str:
    # Basic function to provide an organization id for the test
    # org id from https://labelbox.atlassian.net/wiki/spaces/PLT/pages/2110816271/How+to+labelbox-python+SDK+CI+Tests
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


