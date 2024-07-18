from lbox.cli.main import init


class TestArt:
    def test_init(self):
        assert init() == "init"
