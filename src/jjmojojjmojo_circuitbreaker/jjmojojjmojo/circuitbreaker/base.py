import time
import logging
import random

STATUS_OPEN = 0
STATUS_CLOSED = 1

from .errors import CircuitBreakerOpen, BackendKeyNotFound
from .drivers import Driver

def rand_int_jitter():
    """
    Generate jitter using random.randint().
    """
    return random.randint(0, 10)

class CircuitBreaker:
    """
    A wrapper class for external services. When a service call (passed as a 
    callable object) fails with an exception, the circuit breaker will log the
    failure. When the number of failures exceeds the configured count, the 
    breaker will "open", raising an exception whenever its called, until the 
    configured timeout has elapsed. When the timeout has elapsed, the breaker 
    will be in the "half-open" state, and the next call will be sent along to 
    the external service. If it succeeds, the breaker goes back to "closed", the 
    failure count is reset to 0, and all future calls will go directly to the 
    service, until there are errors again.
    """
    def __init__(self, driver, subject, key, failures=5, timeout=10, jitter=None):
        """
        Constructor.
        
        Parameters:
            - driver, Driver object, required. An implementation of the Driver 
              class from the drivers module, used for storing the state of the 
              CircuitBreaker instance.
            - subject, callable, required - the function to wrap in circuit breaker
              logic.
            - key, string, required - the key that will be used to store the circuit
              breaker state in Redis.
            - redis_url, string, conditional - connection string for Redis. Required
              if 'redis' isn't provided.
            - redis, redis.StrictRedis (or similar) object, conditional. Used to
              connect to redis. Required if 'redis_url' is not provided.
            - failures, int, defaults to 5 - number of failures that will trigger
              the breaker to open
            - timeout, int, defaults to 10 - number of seconds to wait when the
              the breaker is open, before trying the 'subject' again. If the
              subject succeeds, the breaker will close again.
            - jitter, callable to add jitter to the timeout, prevents "stampeding herd"
              issues. Takes no params, returns a number to add to the timeout check.
        """
        self.subject = subject
        self.key = key
        self.max_failures = failures
        self.timeout = timeout
        
        if isinstance(driver, Driver):
            self.driver = driver
        else:
            raise AttributeError("'driver' parameter must be derived from the Driver base class")
        
        self.failures = 0
        self.checkin = time.time()
        self.status = STATUS_CLOSED
        
        self.key = key
        
        self.logger = logging.getLogger("CircuitBreaker")
        
        if jitter is None:
            self._jitter = rand_int_jitter
        else:
            self._jitter = jitter
            
        self._last_jitter = None
        
    @property
    def jitter(self):
        self.logger.debug("Generating jitter")
        if callable(self._jitter):
            jitter = self._jitter()
            self.logger.debug("Jitter is a callable. Returned %s", jitter)
        else:
            jitter = self._jitter
            self.logger.debug("Jitter is a value, '%s'", jitter)
            
        
        self._last_jitter = jitter
        return jitter
        
    def load(self):
        self.driver.expire(self.key, self.checkin)
        
        self.logger.debug("Loading %s", self.key)
        
        try:
            info = self.driver.load(self.key)
            self.logger.debug("%s found", self.key)
        except BackendKeyNotFound:
            self.logger.debug("Entry %s not found, creating a new one", self.key)
            info = self.driver.new(self.key)
        
        self.failures = info["failures"]
        self.checkin = info["checkin"]
        self.status = info["status"]
        
    def failure(self):
        self.logger.debug("Logging failure for %s", self.key)
        self.failures = self.driver.failure(self.key)
        
    def save(self):
        """
        Update this breaker's state.
        """
        self.logger.debug("Saving %s", self.key)
        self.checkin = time.time()
        self.driver.update(
            key=self.key,
            failures=self.failures,
            status=self.status,
            checkin=self.checkin)
        
    def reset(self):
        """
        Reset the breaker to the closed state, reset failure count, re-checkin
        """
        self.logger.debug("Resetting %s", self.key)
        self.driver.reset(self.key)
        
    def open(self):
        """
        Open the breaker.
        """
        if self.status == STATUS_CLOSED:
            self.logger.info("Opening %s", self.key)
            self.driver.open(self.key)
            self.status = STATUS_OPEN
            self.checkin = self.driver.now()
    
    def close(self):
        """
        Close, and reset the breaker
        """
        if self.status == STATUS_OPEN:
            self.logger.info("Closing %s", self.key)
            self.driver.close(self.key)
            self.status = STATUS_CLOSED
    
    def _try_or_open(self, *args, **kwargs):
        """
        Helper method. 
        
        Attempts to call self.subject. If it throws an exception, it logs the 
        failure. If it doesn't, it closes the breaker and returns the result.
        
        If a failure is logged, the number of failures is checked, and if it 
        exceeds self.max_failures, the breaker is opened. 
        
        Raises CircuitBreakerOpen if the breaker has flipped.
        """
        self.logger.debug("Trying to execute service for %s", self.key)
        
        try:
            result = self.subject(*args, **kwargs)
            self.close()
            return result
        except Exception as e:
            self.logger.error("Error detected accessing %s: %s", self.key, e)
            self.failure()
            
            self.logger.debug("Maximum failures %s *not* exceeded. Re-raising", self.max_failures)
            raise
    
    def __call__(self, *args, **kwargs):
        """
        Execute the subject callable, and implement the circuit breaker logic.
        
        Raises CircuitBreakerOpen in the event that the breaker is in the "open"
        state. This signals to the caller that the breaker is open and they should
        retry the call again.
        
        All positional and keyword arguments are passed verbatim to the subject
        callable.
        """
        self.load()
        
        if self.status == STATUS_OPEN:
            self.logger.debug("Breaker %s is OPEN", self.key)
            if self.driver.now() - self.checkin >= self.timeout+self.jitter:
                self.logger.info("Timeout reached. Retrying %s. Jitter %s", self.key, self._last_jitter)
                return self._try_or_open(*args, **kwargs)
            else:
                raise CircuitBreakerOpen()
        
        if self.status == STATUS_CLOSED:
            if self.failures >= self.max_failures:
                self.logger.debug("Maximum failures %s exceeded.", self.max_failures)
                self.open()
                raise CircuitBreakerOpen()
            self.logger.debug(f"Breaker %s is CLOSED", self.key)
            return self._try_or_open(*args, **kwargs)
            
    def dict(self):
        """
        A representation of this object as a dictionary of simple values.
        """
        return {
            'key': self.key,
            'status': self.status,
            'failures': self.failures,
            'timeout': self.timeout,
            'checkin': self.checkin,
            'jitter': self._last_jitter,
            'max_failures': self.max_failures
        }
        
            
    def __repr__(self):
        """
        A representation of this object for use when printing - handy for interpreter
        use.
        """
        if self.status == STATUS_CLOSED:
            status = "CLOSED"
        elif self.status == STATUS_OPEN:
            status = "OPEN"
        else:
            status = "UNKNOWN"
        return f"<{self.__class__.__name__} [{self.key}] status={status} failures={self.failures} checkin={self.checkin}, jitter={self._last_jitter}>"
