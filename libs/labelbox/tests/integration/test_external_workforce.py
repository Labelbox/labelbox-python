from labelbox import Project, ExternalWorkforce
import os


def test_add_external_workforce(project: Project):
    # org id from https://labelbox.atlassian.net/wiki/spaces/PLT/pages/2110816271/How+to+labelbox-python+SDK+CI+Tests
    workforce_id = "clum46jsb00jp07z338dh1gvb" if os.environ['LABELBOX_TEST_ENVIRON'] == "staging" else "ckcz6bubudyfi0855o1dt1g9s"
    
    external_workforces = project.add_external_workforce(workforce_id)
    assert len(external_workforces) == 1
    assert isinstance(external_workforces[0], ExternalWorkforce)


def test_get_external_workforces(project: Project):
    external_workforces = project.get_external_workforces()
    assert len(external_workforces) == 1
    assert isinstance(external_workforces[0], ExternalWorkforce)


def test_remove_external_workforce(project: Project):
    # org id from https://labelbox.atlassian.net/wiki/spaces/PLT/pages/2110816271/How+to+labelbox-python+SDK+CI+Tests
    workforce_id = "clum46jsb00jp07z338dh1gvb" if os.environ['LABELBOX_TEST_ENVIRON'] == "staging" else "ckcz6bubudyfi0855o1dt1g9s"

    external_workforces = project.remove_external_workforce(workforce_id)
    assert len(external_workforces) == 0


