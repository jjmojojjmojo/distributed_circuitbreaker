"""
Return a random dog picture, from https://random.dog

see: https://github.com/AdenFlorian/random.dog
"""
from jjmojojjmojo.circuitbreaker import RedisCircuitBreaker, errors
from jjmojojjmojo.circuitbreaker.tests.util import IntermittentFailer, Failure
import requests
from webob import Request, Response
from webob.static import DirectoryApp
import os
import logging

# construct an absolute path to where we've stored the single page application
# assets.
static_dir = os.path.join(os.path.dirname(__file__), "static")

def random_dog():
    """
    Super-simple remote web request using the requests library.
    
    Returns a dictionary that contans a single member 'url', 
    containing a direct link to a random picture or video of a dog.
    """
    r = requests.get("https://random.dog/woof.json")
    return r.json()

class App:
    """
    Minimalistic WSGI App.
    """
    def __init__(self, redis_url):
        """
        Constructor - sets up the RedisCircuitBreaker using an IntermittentFailer
        to ensure it fails at a predictable rate.
        
        You may want to fiddle with the configuration of the failer to produce 
        different failure patterns.
        """
        self.random_dog = RedisCircuitBreaker(
            subject=IntermittentFailer(random_dog, 5, 8),
            redis_url=redis_url,
            key="random.dog",
            failures=5,
            timeout=10,
            expires=300)
        
        # a cache for the last dog that was successfully retrieved.
        self.last_dog = None
            
    def front_end(self):
        """
        All of the single-page application assets are delivered using
        WebOb's DirectoryApp.
        """
        return DirectoryApp(static_dir)
        
    def get_dog(self):
        """
        Create a response that returns a random dog url as a JSON string.
        
        It also adds some extra information from the CircuitBreaker so the 
        front-end can display some debugging details and you can keep an eye 
        on what's going on in the breaker.
        
        If the breaker is closed, the last dog url that was retrieved is sent.
        
        This is accomplished by stashing the last result from random.dog in an
        instance variable called last_dog.
        
        In the event of an exception (any exception), the status code is changed
        to 500 and the status is set to "error"
        """
        response = Response()
        
        response.status = 200
        response.content_type = "application/json";
        
        status = "ok"
        
        try:
            self.last_dog = self.random_dog()
        except errors.CircuitBreakerOpen:
            status = "breaker-open"
        except Exception:
            response.status = 500
            status = "error"
            
        response.json = {
            'dog': self.last_dog,
            'status': status,
            'cb': self.random_dog.dict()
        }
        
        return response
            
    def __call__(self, environ, start_response):
        """
        Main entry point to the application.
        
        Handles routing - /dog is the API end point for retrieving a random
                               dog
                        - / maps to the static assets for the signle-page app.
        """
        request = Request(environ)
        
        if self.last_dog is None:
            self.last_dog = {
               "url": request.relative_url("/static/images/default-peanut.jpg")
            }
        
        if request.path == "/dog":
            response = self.get_dog()
        else:
            response = self.front_end()
            
        return response(environ, start_response)
        

# set the log level via the $LOGLEVEL environment variable
loglevel = os.environ.get("LOGLEVEL", "debug").upper()

# make the logging match Gunicorn.
logging.basicConfig(
    format="%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S %z]",
    level=getattr(logging, loglevel))

# make an instance for gunicorn (or the WSGI server of your choice) to use.
# uses the default location for Redis.
app = App("redis://localhost:6379/0")