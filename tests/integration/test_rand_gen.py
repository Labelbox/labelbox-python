from labelbox import Project

def test_gen_str(rand_gen):
    assert isinstance(rand_gen(Project.name), str)
    assert len({rand_gen(Project.name) for _ in range(100)}) == 100
