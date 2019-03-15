"""
Helpful utility functions/classes for testing.
"""
from ..drivers import MemoryDriver
from .. import errors
import time

class Failure(Exception):
    """
    Class used by the IntermittentFailer.
    """
    pass

class InitialFailure(Failure):
    """
    Used to separate initial failures from continuing failures.
    """
    pass

class ExtraFailure(Failure):
    """
    Used to indicate a failure is after the initial one.
    """
    pass

def fail(*args, **kwargs):
    """
    A callable that will always fail with an exception.
    """
    raise Exception
    
def succeed(*args, **kwargs):
    """
    A callable that will always succeed.
    """
    return True

def cycle(iterator):
    """
    Cycles through the given iterable forever
    """
    while True:
        for member in iterator:
            yield member
            
class Cycle:
    """
    Identical in function to cycle() above, but provides access to the current index.
    """
    def __init__(self, iterator):
        self.iterator = iterator
        self.index = -1
    
    def __iter__(self):
        return self
    
    def __next__(self):
        try:
            self.index += 1
            obj = self.iterator[self.index]
        except IndexError:
            self.index = 0
            obj = self.iterator[0]
        
        return obj

class IntermittentFailer:
    """
    Callable that will fail intermittently at a predictable rate.
    
    The fail/succeed pattern is generated (if it's not provided) from the 
    parameters.
    
    Internally, the fail/succeed pattern is a iterable that is wrapped in a Cycle 
    object so that each time next() is called, it will produce the next value.
    """
    def __init__(self, to_return=True, frequency=5, fail_count=1, pattern=None, on_fail=Failure):
        """
        to_return: object, if callable, this object will be called when the IntermittentFailer
               succeeds. If a non-callable, the object is returned verbatim.
        frequency: The call number when the first failure occurs.
        fail_count: once the first failure occurs, keep failing for this many calls.
        pattern: bypass frequency and fail_count, and provide an iterable of True/False values
        on_fail: provide a custom exception class to raise instead of the default.
        """
        if pattern is None:
            pattern = []
            for i in range(frequency-1):
                pattern.append(True)
            
            for i in range(fail_count):
                pattern.append(False)
        
        self._pattern = Cycle(pattern)
        self._orig_pattern = pattern
        
        self.on_fail = on_fail
        
        self.to_return = to_return
        self.frequency = frequency
        self.fail_count = fail_count
    
    @property
    def pattern(self):
        """
        Retrieve the next item in the pattern.
        """
        return next(self._pattern)
        
    def __call__(self, *args, **kwargs):
        if self.pattern:
            if callable(self.to_return):
                return self.to_return()
            else:
                return self.to_return
        else:
            raise self.on_fail()
            
    def dict(self):
        """
        Return useful debugging information as a dictionary.
        """
        return {
            'pattern': self._orig_pattern,
            'frequency': self.frequency,
            'fail_count': self.fail_count,
            'index': self._pattern.index
        }
            
    def __repr__(self):
        return f"<IntermittentFailer {self._orig_pattern} f/r: {self.frequency}/{self.fail_count} index:{self._pattern.index}>"

class AlwaysFailDriver(MemoryDriver):
    """
    A driver that raises DistributedBackendProblem, with different actions
    """
    def __init__(self, expires=None, fail_on="load"):
        """
        fail_on: string, indicates when the driver should fail. Possible values are:
                    - "load", when the load() method is called
                    - "update", when the update() method is called
                    - "failure", when the failure() method is called
                    - "all" when any of the three above methods are called.
        """
        MemoryDriver.__init__(self, expires)
        
        self.fail_on = fail_on
        
    def load(self, key):
        if self.fail_on in ("load", "all"):
            raise errors.DistributedBackendProblem()
        else:
            return MemoryDriver.load(self, key)
        
    def update(self, key, failures=None, status=None, checkin=None):
        if self.fail_on in ("update", "all"):
            raise errors.DistributedBackendProblem()
        else:
            return MemoryDriver.update(self, key, failures=failures, status=status, checkin=checkin)
        
    def failure(self, key):
        if self.fail_on in ("failure", "all"):
            raise errors.DistributedBackendProblem()
        else:
            return MemoryDriver.failure(self, key)