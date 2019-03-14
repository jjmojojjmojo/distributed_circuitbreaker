from locust import HttpLocust, Locust, TaskSet, task, events
from datetime import datetime
import logging

from conftest import wait_for_port
import redis
import subprocess
import os

logger = logging.getLogger("timestamp")

def logging_handler(request_type, name, response_time, response_length, **kw):
    """
    Quick hack to log the request timestamp along with the response time.
    """
    now = datetime.now()
    logger.info("%s count: %s", now, response_time)
    
#events.request_success += logging_handler
#events.request_failure += logging_handler

class UserBehavior(TaskSet):
    def setup(self):
        module_dir = os.path.dirname(os.path.realpath(__file__))
        
        app_port = 9234
        redis_port = 6380
        
        self.redis_url = f"redis://127.0.0.1:{redis_port}/9"
        
        self.redis_process = subprocess.Popen(f"redis-server --port {redis_port}".split())
        
        wait_for_port(redis_port)
        
        con = redis.StrictRedis.from_url(self.redis_url)
        con.flushall()
        
        self.app_process = subprocess.Popen(f"python {module_dir}/server.py -w 10 -r {self.redis_url} -p {app_port} failing".split())
        wait_for_port(app_port)
        
    def teardown(self):
        self.app_process.terminate()
        self.redis_process.terminate()
    
    @task(1)
    def post(self):
        self.client.post("/")

class WebsiteUser(HttpLocust):
    host = "http://127.0.0.1:9234"
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000