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

class MemoryCircuitBreaker(CircuitBreaker):
    def __init__(self, subject, key, expires=180, failures=5, timeout=10, jitter=None):
        driver = MemoryDriver(expires=expires)
        
        CircuitBreaker.__init__(
            self,
            driver=driver,
            subject=subject,
            key=key,
            failures=failures,
            timeout=timeout,
            jitter=jitter)

class RedisCircuitBreaker(CircuitBreaker):
    """
    Compositon class that provides a Redis-based driver for the CircuitBreaker
    class.
    """

    def __init__(self, subject, key, expires=180, redis_url=None, redis_connection=None, failures=5, timeout=10, jitter=None, prefix="rcb:"):
        """
        This constructor is a simple extension of the CircuitBreaker base.
        
        Special arguments:
           - redis_url: string, see RedisDriver
           - redis_connection: StrictRedis object, see RedisDriver
        """
        driver = RedisDriver(redis_url=redis_url, redis_connection=redis_connection, expires=expires, prefix=prefix)
        
        CircuitBreaker.__init__(
            self, 
            driver=driver, 
            subject=subject, 
            key=key, 
            failures=failures, 
            timeout=timeout,
            jitter=jitter)