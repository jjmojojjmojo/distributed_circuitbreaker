"""
A simple in-memory implementation of a CircuitBreaker Driver class.
"""

from .base import Driver, STATUS_OPEN, STATUS_CLOSED
from ..errors import BackendKeyNotFound
import time
import logging

class MemoryDriver(Driver):
    """
    Simple in-memory storage.
    
    Uses an internal dictionary to store circuit breaker state.
    """
    def __init__(self, expires=None):
        Driver.__init__(self, expires)
        self.state = {}
        
    def failure(self, key):
        try:
            self.state[key]['failures'] += 1
        except KeyError:
            raise BackendKeyNotFound(f"{key} not in internal store")
            
        return self.state[key]['failures']
        
    def delete(self, key):
        try:
            del self.state[key]
        except KeyError:
            raise BackendKeyNotFound(f"{key} not in internal store")
        
    def update(self, key, failures=None, status=None, checkin=None):
        to_update = {}
        
        if failures is not None:
            to_update['failures'] = failures
        if status is not None:
            to_update['status'] = status
        if checkin is not None:
            to_update['checkin'] = checkin
                
        try:
            self.state[key].update(to_update)
        except KeyError:
            self.state[key] = self.default()
            self.state[key].update(to_update)
        
    def load(self, key):
        try:
            return self.state[key]
        except KeyError:
            raise BackendKeyNotFound(f"{key} not in internal store")