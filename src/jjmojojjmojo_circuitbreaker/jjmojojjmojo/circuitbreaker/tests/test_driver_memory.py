"""
Unit Tests for the MemoryDriver back-end.
"""

from ..drivers import MemoryDriver
from ..base import STATUS_OPEN, STATUS_CLOSED
from ..errors import BackendKeyNotFound
from . import util
import time
import pytest

def test_basic_operation():
    """
    Typical use case
    """
    driver = MemoryDriver(expires=10)
    
    with pytest.raises(BackendKeyNotFound):
        driver.load("hello")
        
    driver.state["hello"] = driver.default()
    
    driver.failure("hello")
    
    assert driver.state['hello']['failures'] == 1
    assert driver.state['hello']['status'] == STATUS_CLOSED
    
    driver.open("hello")
    
    assert driver.state["hello"]["status"] == STATUS_OPEN
    
    driver.close("hello")
    
    assert driver.state["hello"]["status"] == STATUS_CLOSED
    
    
    driver.failure("hello")
    driver.close("hello")
    
    assert driver.state['hello']['failures'] == 0
    assert driver.state['hello']['status'] == STATUS_CLOSED
    
    driver.open("hello")
    driver.reset("hello")
    
    assert driver.state["hello"]["failures"] == 0
    assert driver.state['hello']['status'] == STATUS_CLOSED
    
    driver.delete('hello')
    
    assert "hello" not in driver.state
    
    with pytest.raises(BackendKeyNotFound):
        driver.failure("hello")
        
    with pytest.raises(BackendKeyNotFound):
        driver.delete("hello")

def test_expiry():
    """
    Make sure that the storage expires.
    """
    
    driver = MemoryDriver(expires=1)
    
    driver.state["hello"] = driver.default()
    
    time.sleep(1)
    
    driver.expire("hello", driver.state["hello"]["checkin"])
    
    assert "hello" not in driver.state