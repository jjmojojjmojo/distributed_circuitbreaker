import logging
from ..base import STATUS_OPEN, STATUS_CLOSED
from ..errors import BackendKeyNotFound, BackendKeyHasExpired
import time

class Driver:
    def __init__(self, expires=None):
        self.expires = expires
        self.logger = logging.getLogger(f"CircuitBreaker:{self.__class__.__name__}")
    
    def default(self):
        return {
            'failures': 0,
            'status': STATUS_CLOSED,
            'checkin': self.now()
        }
    
    def now(self):
        return time.time()
        
    def new(self, key):
        """
        Create a new record in the store, return its data.
        """
        info = self.default()
        self.update(key, **info)
        return info
        
    def expire(self, key, checkin):
        if self.expires is not None:
            if self.now() - checkin >= self.expires:
                self.delete(key)
        
    def checkin(self, key):
        self.update(key, checkin=self.now())
    
    def failure(self, key):
        pass
    
    def delete(self, key):
        pass
    
    def update(self, key, failures=None, status=None, checkin=None):
        pass
    
    def close(self, key):
        self.update(key, status=STATUS_CLOSED, failures=0, checkin=self.now())
        
    def open(self, key):
        self.update(key, status=STATUS_OPEN, checkin=self.now())
        
    def reset(self, key):
        self.update(key, failures=0, status=STATUS_CLOSED, checkin=self.now())
    
    def load(self, key):
        pass