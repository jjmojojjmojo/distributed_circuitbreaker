"""
Functional tests for the redis driver backend.
"""

from jjmojojjmojo.circuitbreaker import STATUS_OPEN, STATUS_CLOSED
from jjmojojjmojo.circuitbreaker.drivers import RedisDriver
from jjmojojjmojo.circuitbreaker.errors import DistributedBackendProblem, BackendKeyNotFound
import pytest
from util import PREFIX
import time


def test_load_no_data(redis_url):
    driver = RedisDriver(redis_url=redis_url)
    
    with pytest.raises(BackendKeyNotFound):
        driver.load("test")
        
def test_load_existing(conn_with_preload_data):
    """
    Test loading when there is data already in the DB
    """
    conn, checkin = conn_with_preload_data
    
    driver = RedisDriver(redis_connection=conn, prefix=PREFIX)
    
    info = driver.load("test1")
    
    assert info["failures"] == 0
    assert info["checkin"] == checkin
    assert info["status"] == STATUS_CLOSED
    
    info = driver.load("ftest4")
    
    assert info["failures"] == 2
    assert info["checkin"] == checkin
    assert info["status"] == STATUS_OPEN
    
def test_failure(conn_with_preload_data):
    """
    Test logging a failure, data exists.
    """
    conn, checkin = conn_with_preload_data
    
    driver = RedisDriver(redis_connection=conn, prefix=PREFIX)
    
    out = driver.failure("test1")
    
    assert out == 1
    
    info = driver.load("test1")
    
    assert info["failures"] == 1
    
def test_open(conn_with_preload_data):
    """
    Test opening a breaker, data exists.
    """
    conn, checkin = conn_with_preload_data
    
    driver = RedisDriver(redis_connection=conn, prefix=PREFIX)
    
    driver.open("test1")
    
    info = driver.load("test1")
    
    assert info["status"] == STATUS_OPEN
    
def test_close(conn_with_preload_data):
    """
    Test closing a breaker, data exists.
    """
    conn, checkin = conn_with_preload_data
    
    driver = RedisDriver(redis_connection=conn, prefix=PREFIX)
    
    driver.close("test1")
    
    info = driver.load("test1")
    
    assert info["status"] == STATUS_CLOSED
    
def test_delete(conn_with_preload_data):
    """
    Test deleting an entry
    """
    conn, checkin = conn_with_preload_data
    
    driver = RedisDriver(redis_connection=conn, prefix=PREFIX)
    
    driver.delete("test1")
    
    with pytest.raises(BackendKeyNotFound):
        driver.load("test1")
        
def test_expiry(conn_with_preload_data):
    """
    Let an entry expire
    """
    conn, checkin = conn_with_preload_data
    
    driver = RedisDriver(expires=1, redis_connection=conn, prefix=PREFIX)
    
    driver.new("expireme")
    
    time.sleep(1.5)
    
    with pytest.raises(BackendKeyNotFound):
        driver.load("expireme")