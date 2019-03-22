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

static_dir = os.path.join(os.path.dirname(__file__), "static")

def random_dog():
    r = requests.get("https://random.dog/woof.json")
    return r.json()

class App:
    def __init__(self, redis_url):
        self.random_dog = RedisCircuitBreaker(
            subject=IntermittentFailer(random_dog, 10, 20),
            redis_url=redis_url,
            key="random.dog",
            failures=15,
            timeout=60,
            expires=300)
        
        self.last_dog = None
            
    def front_end(self):
        return DirectoryApp(static_dir)
        
    def get_dog(self):
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
        request = Request(environ)
        
        if self.last_dog is None:
            self.last_dog = {
                "dog": request.relative_url("/static/images/default-peanut.jpg")
            }
            
            print(self.last_dog)
        
        if request.path == "/dog":
            response = self.get_dog()
        else:
            response = self.front_end()
            
        return response(environ, start_response)
        
app = App("redis://localhost:6379/0")