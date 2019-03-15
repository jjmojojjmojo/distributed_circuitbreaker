"""
jjmojojjmojo.circuitbreaker
===========================

A simple implementation of a Distributed version of the Circuit Breaker Pattern
from "Release It!" by Michael Nygard.

The distributed features were developed using Redis as a back-end, but the 
library is structured to work with "drivers", so any conceivable backend can be
created.

The library acts as a "wrapper" around any callable so robust versions of 
existing functions can be easily built.
"""

from .base import CircuitBreaker, STATUS_OPEN, STATUS_CLOSED
from .drivers import RedisDriver, MemoryDriver

def MemoryCircuitBreaker(key, subject, expires=180, failures=5, timeout=10, jitter=None):
    """
    Create a ready-to-go CircuitBreaker with a MemoryDriver driver.
    """
    driver = MemoryDriver(expires=expires)
    
    breaker = CircuitBreaker(
        driver=driver,
        subject=subject,
        key=key,
        failures=failures,
        timeout=timeout,
        jitter=jitter)
    
    return breaker

def RedisCircuitBreaker(key, subject, expires=180, failures=5, timeout=10, jitter=None, redis_url=None, redis_connection=None, prefix="rcb:"):
    """
    Create and configure a CircuitBreaker with a RedisDriver back-end.
    
    Special arguments:
       - redis_url: string, see RedisDriver
       - redis_connection: StrictRedis object, see RedisDriver
       - prefix: a string to help group the circuit breaker keys in redis.
    """
    driver = RedisDriver(
        redis_url=redis_url, 
        redis_connection=redis_connection, 
        expires=expires, 
        prefix=prefix)
        
    breaker = CircuitBreaker(
        driver=driver, 
        subject=subject, 
        key=key, 
        failures=failures, 
        timeout=timeout,
        jitter=jitter)
    
    return breaker