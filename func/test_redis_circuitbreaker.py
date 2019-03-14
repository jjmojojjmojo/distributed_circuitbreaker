"""
Integration test for the RedisCircuitBreaker class
"""

from jjmojojjmojo.circuitbreaker import STATUS_OPEN, STATUS_CLOSED, RedisCircuitBreaker
from jjmojojjmojo.circuitbreaker.errors import CircuitBreakerOpen
import pytest
from jjmojojjmojo.circuitbreaker.tests.util import IntermittentFailer, Failure
import time
from util import PREFIX

def test_basic_functionality_no_data(conn_with_preload_data):
    """
    Basic "happy path" functionality. Data doesn't currently exist.
    """
    conn, checkin = conn_with_preload_data
    
    failer = IntermittentFailer(frequency=3, fail_count=11)
    
    breaker = RedisCircuitBreaker(
        timeout=5,
        key="testZ", 
        subject=failer,
        expires=5,
        failures=10,
        redis_connection=conn)
        
    assert breaker() == True
    assert breaker() == True
    
    for i in range(10):
        with pytest.raises(Failure):
            breaker()
    # assert False        
    with pytest.raises(CircuitBreakerOpen):
        breaker()
        
    with pytest.raises(CircuitBreakerOpen):
        breaker()
        
    time.sleep(5)
    
    with pytest.raises(Failure):
        breaker()
        
    assert breaker() == True
    assert breaker() == True
    
    with pytest.raises(Failure):
        breaker()
    
def test_basic_func_existing_data(conn_with_preload_data):
    """
    Basic "happy path" functionality. Data exists.
    """
    conn, checkin = conn_with_preload_data
    
    failer = IntermittentFailer(frequency=3, fail_count=11)
    
    # already has 2 failures logged, breaker is OPEN
    breaker = RedisCircuitBreaker(
        timeout=5,
        key="ftest6", 
        subject=failer,
        expires=10,
        failures=10,
        redis_connection=conn, 
        prefix=PREFIX,
        jitter=0)
    
    with pytest.raises(CircuitBreakerOpen):
        breaker()
        
    time.sleep(6)
    
    assert breaker() == True
    
    assert breaker() == True
    
    for i in range(10):
        with pytest.raises(Failure):
            breaker()
            
    
    with pytest.raises(CircuitBreakerOpen):
        breaker()
        
    with pytest.raises(CircuitBreakerOpen):
        breaker()
        
    time.sleep(15)
    
    with pytest.raises(Failure):
        breaker()
        
    assert breaker() == True
    assert breaker() == True
    
    with pytest.raises(Failure):
        breaker()