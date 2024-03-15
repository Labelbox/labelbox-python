from labelbox import utils

SNAKE = "this_is_a_string"
TITLE = "ThisIsAString"
CAMEL = "thisIsAString"
MIXED = "this_Is_AString"


def test_camel():
    assert utils.camel_case(SNAKE) == CAMEL
    assert utils.camel_case(TITLE) == CAMEL
    assert utils.camel_case(CAMEL) == CAMEL
    assert utils.camel_case(MIXED) == CAMEL


def test_snake():
    assert utils.snake_case(SNAKE) == SNAKE
    assert utils.snake_case(TITLE) == SNAKE
    assert utils.snake_case(CAMEL) == SNAKE
    assert utils.snake_case(MIXED) == SNAKE


def test_title():
    assert utils.title_case(SNAKE) == TITLE
    assert utils.title_case(TITLE) == TITLE
    assert utils.title_case(CAMEL) == TITLE
    assert utils.title_case(MIXED) == TITLE
