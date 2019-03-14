"""
Web Server To Run Functional/Integration Tests
"""

import gunicorn.app.base
from jjmojojjmojo.circuitbreaker import RedisCircuitBreaker, MemoryCircuitBreaker
from jjmojojjmojo.circuitbreaker.errors import CircuitBreakerOpen
from jjmojojjmojo.circuitbreaker.tests.util import IntermittentFailer, Failure
import logging
import argparse
import pprint
import json
from webob import Request, Response
import random, time, os


def benevolent_callable():
    """
    A function that always returns True.
    """
    return time.time()

class CircuitBreakerApp:
    """
    WSGI application using the RedisCircuitBreaker class.
    
    Pretends to be a RESTish end point, returning JSON. 
    
    The app caches the last value from the subject, to help ensure the back-end
    isn't actually getting called, you can compare multiple responses and ensure
    it hasn't changed.
    """
    def __init__(self, breaker_class, **kwargs):
        self.cache = None
        
        if kwargs["jitter"] is None:
            kwards["jitter"] = 0
            
        print(kwargs)
        
        # if 0 or False is passed, turn off expiration
        if not kwargs["expires"]:
            kwargs["expires"] = None
        
        self.cb = breaker_class(**kwargs)
    
    def __call__(self, environ, start_response):
        req = Request(environ)
        
        out = {
            'code': "",
            'value': ""
        }
        
        res = Response()
        
        if req.path == "/reset":
            self.cb.reset()
            res.json = {'reset': 1}
            return res(environ, start_response)
        
        try:
            self.cache = self.cb()
        except Failure:
            out['code'] = "back-end-failure"
            out['value'] = self.cache
        except CircuitBreakerOpen:
            out['code'] = "circuitbreaker-open"
            out['value'] = self.cache
        else:
            out['code'] = "ok"
            out['value'] = self.cache
            
        
        out['breaker-info'] = self.cb.dict()
        
        out['expires'] = self.cb.driver.expires
        
        if isinstance(self.cb.subject, IntermittentFailer):
            out['failer-info'] = self.cb.subject.dict()
        
        res.json = out
        return res(environ, start_response)

class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

parser = argparse.ArgumentParser(description='Test server.')
parser.add_argument('-p', '--port', type=int, default=8909)
parser.add_argument('-r', '--redis-url', type=str, default="redis://localhost:6379/0")
parser.add_argument('-e', '--expires', type=int, default=10)
parser.add_argument('-l', '--log-level', type=str, default="info")
parser.add_argument('-f', '--cb-failures', type=int, default=5)
parser.add_argument('-t', '--cb-timeout', type=int, default=10)
parser.add_argument('--fail-freq', type=int, default=5)
parser.add_argument('--fail-count', type=int, default=6)
parser.add_argument('-w', '--workers', type=int, default=1)
parser.add_argument('-j', '--jitter', type=int, default=0)
parser.add_argument('-b', '--backend', type=str, default="redis", choices=["redis", "memory"])
parser.add_argument('server', type=str, default="normal", choices=["normal", "failing"])

if __name__ == '__main__':
    opts = parser.parse_args()
    
    loglevel = os.environ.get("LOGLEVEL", opts.log_level).upper()
    
    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=getattr(logging, loglevel))
    
    options = {
        'bind': '%s:%s' % ('127.0.0.1', opts.port),
        'workers': opts.workers,
        'timeout': 99999
    }
    
    breaker_options = {
        'failures': opts.cb_failures,
        'timeout': opts.cb_timeout,
        'expires': opts.expires,
        'jitter': opts.jitter
    }
    
    if opts.backend == "redis":
        breaker_class = RedisCircuitBreaker
        breaker_options["redis_url"] = opts.redis_url
    elif opts.backend == "memory":
        breaker_class = MemoryCircuitBreaker
    else:
        raise AssertionError("Unknown backend")
        
    if opts.server == "failing":
        failer = IntermittentFailer(
            to_return=benevolent_callable,
            frequency=opts.fail_freq,
            fail_count=opts.fail_count)
        
        breaker_options["subject"] = failer
        breaker_options["key"] = "failing-functional-server-test"
    else:
        breaker_options["subject"] = benevolent_callable
        breaker_options["key"] = "normal-functional-server-test"
    
    server = CircuitBreakerApp(breaker_class, **breaker_options)
    
    StandaloneApplication(server, options).run()