"""
Py.test fixtures and other test-related things. Loaded automatically by py.test.
"""

import pytest
import random

@pytest.fixture
def fixed_random():
    """
    Fix the random seed so we can predict things like jitter.
    """
    random.seed(1)
    yield 1
    random.seed()