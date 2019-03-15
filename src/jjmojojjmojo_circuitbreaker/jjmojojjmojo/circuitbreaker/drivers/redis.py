"""
Redis-backed Driver for the CircuitBreaker.
"""

from .base import Driver, STATUS_OPEN, STATUS_CLOSED
import time
from ..errors import DistributedBackendProblem, BackendKeyNotFound
import redis

class RedisDriver(Driver):
    """
    A back-end for CircuitBreaker that uses the Redis key-value store.
    """
    
    def __init__(self, expires=None, redis_connection=None, redis_url=None, prefix="rcb:"):
        """
        redis_connection: a redis connection object (or one that follows its API)
        redis_url: string, connection info for a redis server.
        prefix: string, used to group circuit breaker keys in redis.
        """
        Driver.__init__(self, expires=expires)
        
        self.prefix = prefix
        
        if redis_connection is None:
            if redis_url is None:
                raise AttributeError("You must specify one of redis or redis_url")
            self.redis = redis.StrictRedis.from_url(redis_url)
        else:
            self.redis = redis_connection
            
        self.redis.connection_pool.decode_responses = True
    
    def key(self, key):
        """
        Generate a redis key
        """
        return f"{self.prefix}{key}"
    
    def _set_expiry(self, key):
        """
        Helper function to set the EXPIRE on a given key
        """
        if self.expires is not None:
            self.logger.debug("Setting EXPIRE on '%s'", key)
            self._catch_redis_error("expire", self.key(key), self.expires)
    
    def new(self, key):
        info = Driver.new(self, key)
        self._set_expiry(key)
            
        return info
    
    def reset(self, key):
        Driver.reset(self, key)
        self._set_expiry(key)
    
    def expire(self, key, checkin):
        """
        No-op - expiry is handled by redit's EXPIRE command.
        """
        
    def _catch_redis_error(self, command, *args, **kwargs):
        """
        Centralize the catching and re-raising of any redis-related errors.
        """
        try:
            self.logger.debug("Attempting to execute command '%s'", command)
            return getattr(self.redis, command)(*args, **kwargs)
        except redis.RedisError as e:
            self.logger.error(str(e))
            raise DistributedBackendProblem()
        
    def load(self, key):
        self.logger.debug("Loading %s...", key)
        
        info = self._catch_redis_error('hgetall', self.key(key))
        
        if not info:
            self.logger.debug("Could not find '%s'", key)
            raise BackendKeyNotFound(f"{key} not in database")
            
        output = {
            'failures': int(info[b'failures']),
            'status': int(info[b'status']),
            'checkin': float(info[b'checkin'])
        }
        
        return output
        
    def delete(self, key):
        self.logger.debug("Deleting '%s'...", key)
        self._catch_redis_error('delete', self.key(key))
        
    def update(self, key, failures=None, status=None, checkin=None):
        self.logger.debug("Updating '%s'...", key)
        to_update = {}
        
        if failures is not None:
            to_update['failures'] = failures
            
        if status is not None:
            to_update['status'] = status
            
        if checkin is not None:
            to_update['checkin'] = checkin
            
        if to_update:
            self.logger.debug("Updating [%s] for '%s'", to_update.keys(), key)
            self._catch_redis_error('hmset', self.key(key), to_update)
        else:
            raise ValueError("You must specify one of failures, status, or checkin")
        
    def failure(self, key):
        failures = self._catch_redis_error("hincrby", self.key(key), "failures", 1)
        self.logger.debug("Failure. Count for %s: %s", key, failures)
        return int(failures)
        