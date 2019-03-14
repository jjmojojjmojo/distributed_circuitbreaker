import pytest
import random

@pytest.fixture
def fixed_random():
    random.seed(1)
    yield 1
    random.seed()