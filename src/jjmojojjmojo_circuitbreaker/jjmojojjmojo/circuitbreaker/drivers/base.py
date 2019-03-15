"""
Base class for all CircuitBreaker Drivers.
"""

import logging
from ..base import STATUS_OPEN, STATUS_CLOSED
from ..errors import BackendKeyNotFound, BackendKeyHasExpired
import time

class Driver:
    def __init__(self, expires=None):
        """
        Constructor. 
        
        Creates a logging instance (self.logger) that is automatically named
        after the driver class.
        
        expires: int, number of seconds before the back-end deletes the circuitbreaker
                 data.
        """
        self.expires = expires
        self.logger = logging.getLogger(f"CircuitBreaker:{self.__class__.__name__}")
    
    def default(self):
        """
        Return the initial state of the circuit breaker record, as a dict.
        """
        return {
            'failures': 0,
            'status': STATUS_CLOSED,
            'checkin': self.now()
        }
    
    def now(self):
        """
        Generate a timestamp. Returns a float.
        """
        return time.time()
        
    def new(self, key):
        """
        Create a new record in the store, return its data.
        
        key: string, name of the circuit breaker to create.
        """
        info = self.default()
        self.update(key, **info)
        return info
        
    def expire(self, key, checkin):
        """
        Check if the record for the circuitbreaker at the given key should 
        be expunged, and expunge it.
        
        Assumes that the caller can be trusted to provide an accurate
        value for checkin.
        
        key: string, name of the circuit breaker to test.
        checkin: a timestamp to compare.
        """
        if self.expires is not None:
            if self.now() - checkin >= self.expires:
                self.delete(key)
    
    def failure(self, key):
        """
        Log a single failure.
        
        Provided so that back-ends can utilize more efficient queries than 
        self.update() might use.
        
        key: string, name of the circuit breaker to log a failure for.
        """
        pass
    
    def delete(self, key):
        """
        Remove the data for the given circuitbreaker key.
        """
        pass
    
    def update(self, key, failures=None, status=None, checkin=None):
        """
        Update the given circuit breaker. 
        
        This method can take 0 or more keyword arguments. 
        
        If 0 arguments are passed, it is at the discretion of the 
        driver implementation to decide what to do. Suggestion is to
        raise a ValueError.
        
        key: string, circuit breaker to update
        failures: int, number of failures to set the failure count to.
        status: int, one of STATUS_OPEN or STATUS_CLOSED
        checkin: number, timestamp to track when the service that the 
                 breaker wraps is retried.
        """
        pass
    
    def close(self, key):
        """
        Close the given circuit breaker.
        """
        self.update(key, status=STATUS_CLOSED, failures=0, checkin=self.now())
        
    def open(self, key):
        """
        Open the given circuit breaker. Update the checkin.
        """
        self.update(key, status=STATUS_OPEN, checkin=self.now())
        
    def reset(self, key):
        """
        Close the breaker, update checkin, reset the failure count to 0.
        """
        self.update(key, failures=0, status=STATUS_CLOSED, checkin=self.now())
    
    def load(self, key):
        """
        Retrieve the given breaker info from the back-end store.
        
        Raises BackendKeyNotFound if no existing info is present.
        """
        pass