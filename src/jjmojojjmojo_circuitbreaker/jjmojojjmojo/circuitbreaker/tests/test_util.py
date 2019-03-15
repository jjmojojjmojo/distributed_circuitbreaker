"""
Tests for some of the testing utilities 
"""
import pytest
from . import util

def test_cycle():
    """
    Make sure the cycle() utility function works.
    """
    i = range(4)
    
    cycler = util.cycle(i)
    
    assert 0 == next(cycler)
    assert 1 == next(cycler)
    assert 2 == next(cycler)
    assert 3 == next(cycler)
    assert 0 == next(cycler)
    assert 1 == next(cycler)
    assert 2 == next(cycler)
    assert 3 == next(cycler)
    assert 0 == next(cycler)
    
def test_cycle_class():
    """
    Make sure the class-based cycler functions
    """
    i = range(4)
    
    cycler = util.Cycle(i)
    
    assert cycler.index == -1
    
    assert 0 == next(cycler)
    assert 1 == next(cycler)
    assert 2 == next(cycler)
    
    assert cycler.index == 2
    
    assert 3 == next(cycler)
    assert 0 == next(cycler)
    
    assert cycler.index == 0
    
    assert 1 == next(cycler)
    assert 2 == next(cycler)
    assert 3 == next(cycler)
    assert 0 == next(cycler)
    

def test_intermittent_failer_defaults():
    """
    This code is a little complex, so lets make sure it works.
    """
    
    # defaults - fail once every fifth call
    failer = util.IntermittentFailer()
    
    assert failer() == True
    assert failer() == True
    assert failer() == True
    assert failer() == True
    # should initially fail
    with pytest.raises(util.Failure):
        failer()
        
    # do it again to make sure it still works
    assert failer() == True
    assert failer() == True
    assert failer() == True
    assert failer() == True
    with pytest.raises(util.Failure):
        failer()
        
    assert failer() == True

def test_intermittent_failer_many_iterations():
    """
    Run it a looong time, see what happens
    """
    # Every other call will fail, then fail once more.
    failer = util.IntermittentFailer(frequency=2, fail_count=2)
    
    for i in range(2000):
        assert failer() == True
        with pytest.raises(util.Failure):
            failer()
        with pytest.raises(util.Failure):
            failer()
        assert failer() == True
        with pytest.raises(util.Failure):
            failer()
        with pytest.raises(util.Failure):
            failer()
    
def test_intermittent_failer_custom():
    """
    Test various configuration options
    """
    def callme():
        return "hello"
        
    class OnFail(Exception):
        pass
    
    failer = util.IntermittentFailer(to_return=callme)
    
    assert failer() == "hello"
    
    failer = util.IntermittentFailer(pattern=[False,], on_fail=OnFail)
    
    with pytest.raises(OnFail):
        failer()
    