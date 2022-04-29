def test_gen_str(rand_gen):
    assert len({rand_gen(str) for _ in range(100)}) == 100
