class CircuitBreakerException(Exception):
	"""
	Base class for all DCB-related errors
	"""

class BackendKeyHasExpired(CircuitBreakerException):
    """
    Raised when a given key has expired.
    """

class BackendKeyNotFound(CircuitBreakerException):
    """
    Raised when a key is not present in the datastore.
    """

class CircuitBreakerOpen(CircuitBreakerException):
    """
    Thrown when the DCB is called and in the "open" (error) state. 
    
    This signals the caller to try again, return a cached response, etc.
    """
    
class DistributedBackendProblem(CircuitBreakerOpen):
	"""
	Raised when there is some problem with the back-end (redis is down, etc). 
	
	This state is the same as CircuitBreakerOpen, in functional terms.
	"""