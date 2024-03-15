import pytest
from labelbox.data.generator import PrefetchGenerator
from random import random


class ChildClassGenerator(PrefetchGenerator):

    def __init__(self, examples, num_executors=1):
        super().__init__(data=examples, num_executors=num_executors)

    def _process(self, value):
        num = random()
        if num < .2:
            raise ValueError("Randomized value error")
        return value


amount = (i for i in range(50))


def test_single_thread_generator():
    generator = ChildClassGenerator(amount, num_executors=1)

    with pytest.raises(ValueError):
        for _ in range(51):
            next(generator)


def test_multi_thread_generator():
    generator = ChildClassGenerator(amount, num_executors=4)

    with pytest.raises(ValueError):
        for _ in range(51):
            next(generator)
