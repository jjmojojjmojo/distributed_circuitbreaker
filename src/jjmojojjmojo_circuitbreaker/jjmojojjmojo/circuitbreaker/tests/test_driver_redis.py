"""
Unit Tests for the RedisDriver back-end.
"""
from ..drivers.redis import RedisDriver
from ..errors import DistributedBackendProblem
import pytest
import redis

def test_redis_arguments():
    """
    Raise an error if a no redis connection or url is passed.
    """
    with pytest.raises(AttributeError):
        driver = RedisDriver()
        
def test_key_prefix():
    """
    Test the key() method with a given non-default prefix
    """
    driver = RedisDriver(redis_url="redis://", prefix="test:")
    
    assert driver.key("mykey") == "test:mykey"
    
def test_redis_error():
    """
    Run the methods with a bad redis connection
    """
    conn = redis.StrictRedis(host="192.0.2.1", port=9999, db=10, socket_connect_timeout=0.1)
    
    driver = RedisDriver(redis_connection=conn)
    
    with pytest.raises(DistributedBackendProblem):
        driver.load("testkey")
        
    with pytest.raises(DistributedBackendProblem):
        driver.update("testkey", **driver.default())
        
    with pytest.raises(DistributedBackendProblem):
        driver.failure("testkey")
        
    with pytest.raises(DistributedBackendProblem):
        driver.open("testkey")
        
    with pytest.raises(DistributedBackendProblem):
        driver.close("testkey")
        
    with pytest.raises(DistributedBackendProblem):
        driver.delete("testkey")
        
def test_update_without_params():
    """
    Ensure an error is raised when you call update() with nothing to update
    """
    driver = RedisDriver(redis_url="redis://", prefix="test:")
    with pytest.raises(ValueError):
        driver.update("mykey")