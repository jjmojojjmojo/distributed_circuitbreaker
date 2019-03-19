"""
Functional tests - a client talks to a back-end server (see server.py) that uses
the RedisCircuitBreaker.
"""

import requests
import time

class RequestHelper:
    def __init__(self, url):
        self.url = url
        self.previous = None
        self.reset()
        
    def reset(self):
        r = requests.get(self.url+"/reset")
        out = r.json()
        assert out["reset"] == 1
        
    def request(self):
        r = requests.post(self.url)
        return r.json()
        
    def nonfail(self):
        out = self.request()
        assert out["code"] == "ok"
        assert out["value"] != self.previous
        self.previous = out["value"]
        
    def fail(self):
        out = self.request()
        assert out["code"] == 'back-end-failure'
        assert out["value"] == self.previous
        self.previous = out["value"]
        
    def open(self):
        out = self.request()
        assert out["code"] == 'circuitbreaker-open'
        assert out["value"] == self.previous
        self.previous = out["value"]

def test_normal_typical(normal_app):
    """
    Standard functional test - normal operation.
    """
    helper = RequestHelper(normal_app)
    
    for i in range(40):
        helper.nonfail()
        
    time.sleep(11)
    
    for i in range(40):
        helper.nonfail()

 
def test_failing_typical(failing_app):
    """
    Failing operation.
    
    The failing_app fixture is configured to start failing after 4 calls, 
    and then continue failing for 6 more calls.
    """
    helper = RequestHelper(failing_app)
    
    for i in range(4):
        helper.nonfail()
    
    for i in range(5):
        helper.fail()
    
    for i in range(30):
        helper.open()
    
    # wait for circuitbreaker to time out so it will check the back end again
    time.sleep(10)
    
    helper.fail()
    
    # lets do another cycle just to be sure
    for i in range(4):
        helper.nonfail()
    
    for i in range(4):
        helper.fail()
    
    for i in range(60):
        helper.open()