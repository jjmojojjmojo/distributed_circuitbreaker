"""
Unit Tests for the CircuitBreaker class.
"""

from ..base import STATUS_CLOSED, STATUS_OPEN, CircuitBreaker
from ..drivers import MemoryDriver
from .. import errors
import time
import pytest
import random

from . import util

def fail(x):
    """
    Takes one parameter, always fails with a generic exception.
    """
    raise Exception()

def test_basic_breaker():
    """
    Basic "happy path" test.
    """    
    
    # the subject will fail every-other call, 
    # then fail two times in a row.
    failer = util.IntermittentFailer(frequency=2, fail_count=2)
    
    # the breaker opens after 2 failures, and tries again
    # after 5 seconds.
    breaker = CircuitBreaker(
        key="test",
        subject=failer,
        driver=util.MemoryDriver(),
        failures=2,
        timeout=5,
        jitter=lambda: 0)
    
    # first call succeeds
    assert breaker() == True
    
    # second call fails - exception is passed through
    with pytest.raises(util.Failure):
        breaker()
        
    # third call fails - exception is passed through
    with pytest.raises(util.Failure):
        breaker()
        
    # fourth call - breaker is open
    with pytest.raises(errors.CircuitBreakerOpen):
        breaker()
        
    # fifth call - breaker is open
    with pytest.raises(errors.CircuitBreakerOpen):
        breaker()
        
    # sixth call - breaker is open
    with pytest.raises(errors.CircuitBreakerOpen):
        breaker()
    
    # cause the timeout to happen
    time.sleep(6)
    
    # it's working again.
    assert breaker() == True
    
    # just to be sure, it should fail one more time
    with pytest.raises(util.Failure):
        breaker()
    
    
def test_bad_driver():
    """
    Make sure there's an exception if you try to pass a bad driver object.
    """
    with pytest.raises(AttributeError):
        breaker = CircuitBreaker(subject=lambda x: "boo", key="boo", driver=True)
        
def test_backend_problem_all():
    """
    Ensure that the CircuitBreaker class performs as expected when a driver 
    thows DistributedBackendProblem
    """
    driver = util.AlwaysFailDriver(fail_on="all")
    breaker = CircuitBreaker(subject=lambda x: "boo", key="boo", driver=driver)
    
    with pytest.raises(errors.DistributedBackendProblem):
        breaker("hello")
        
    with pytest.raises(errors.DistributedBackendProblem):
        breaker.failure()
        
    with pytest.raises(errors.DistributedBackendProblem):
        breaker.open()
        
    breaker.status = STATUS_OPEN
        
    with pytest.raises(errors.DistributedBackendProblem):
        breaker.close()

def test_backend_problem_update():
    """
    Ensure that the CircuitBreaker class performs as expected when a driver 
    thows DistributedBackendProblem in it's update() method
    """    
    driver = util.AlwaysFailDriver(fail_on="update")
    breaker = CircuitBreaker(
        subject=fail, 
        key="boo", 
        driver=driver,
        failures=2)
    
    with pytest.raises(Exception):
        breaker("hello")
        
    with pytest.raises(Exception):
        breaker("hello")
        
    with pytest.raises(errors.DistributedBackendProblem):
        breaker("hello")

def test_backend_problem_failure():
    """
    Ensure that the CircuitBreaker class performs as expected when a driver 
    thows DistributedBackendProblem in it's failure() method
    """
    driver = util.AlwaysFailDriver(fail_on="failure")
    breaker = CircuitBreaker(subject=lambda x: "boo", key="boo", driver=driver)
    
    breaker = CircuitBreaker(
        subject=fail, 
        key="boo", 
        driver=driver,
        failures=2)
    
    with pytest.raises(Exception):
        breaker("hello")
        
    with pytest.raises(Exception):
        breaker("hello")
        
    with pytest.raises(errors.DistributedBackendProblem):
        breaker("hello")
        
def test_backend_problem_load():
    """
    Ensure that the CircuitBreaker class performs as expected when a driver 
    thows DistributedBackendProblem in it's load() method
    """
    driver = util.AlwaysFailDriver(fail_on="load")
    breaker = CircuitBreaker(subject=lambda x: "boo", key="boo", driver=driver)
    
    with pytest.raises(errors.DistributedBackendProblem):
        breaker("hello")


def test_default_jitter(fixed_random):
    """
    Ensure the default jitter is being executed.
    """
    
    failer = util.IntermittentFailer(frequency=1, fail_count=3)
    
    breaker = CircuitBreaker(
        key="test2", 
        subject=failer,
        driver=util.MemoryDriver(), 
        failures=1, 
        timeout=5)
    
    assert breaker.jitter == 2
    assert breaker.jitter == 9
    
def test_repr(fixed_random):
    """
    Check the __repr__() magic method, and double-check some internal state.
    """
    def failer():
        raise util.Failure
    
    breaker = CircuitBreaker(
        key="test2", 
        subject=failer,
        driver=util.MemoryDriver(), 
        failures=1, 
        timeout=5)
    
    expected = f"<CircuitBreaker [test2] status=CLOSED failures=0 checkin={breaker.checkin}, jitter=None>"
    
    assert expected == repr(breaker)
    
    with pytest.raises(util.Failure):
        breaker()
    
    with pytest.raises(errors.CircuitBreakerOpen):
        breaker()
        
    expected = f"<CircuitBreaker [test2] status=OPEN failures=1 checkin={breaker.checkin}, jitter=None>"
    
    assert expected == repr(breaker)
    
    with pytest.raises(errors.CircuitBreakerOpen):
        breaker()
        
    expected = f"<CircuitBreaker [test2] status=OPEN failures=1 checkin={breaker.checkin}, jitter=2>"
    
    assert expected == repr(breaker)
    
    breaker.close()
    
    breaker.subject = lambda: True
    
    assert breaker() == True
    
    expected = f"<CircuitBreaker [test2] status=CLOSED failures=0 checkin={breaker.checkin}, jitter={breaker.jitter}>"
    
    assert expected == repr(breaker)
    
    breaker.status = 9
    
    expected = f"<CircuitBreaker [test2] status=UNKNOWN failures=0 checkin={breaker.checkin}, jitter={breaker.jitter}>"
    
    assert expected == repr(breaker)