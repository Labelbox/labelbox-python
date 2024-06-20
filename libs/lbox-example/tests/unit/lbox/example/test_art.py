from lbox.example.art import coffee


class TestArt:
    def test_logo(self):
        result = coffee()
        assert result == "c[_]"
