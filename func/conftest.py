"""
Test fixtures.
"""
import pytest
import redis
import subprocess
import time
import socket
import math
import os

from jjmojojjmojo.circuitbreaker import STATUS_OPEN, STATUS_CLOSED

from util import PREFIX

module_dir = os.path.dirname(__file__)

def wait_for_port(port):
    """
    Block until a TCP port can be connected to.
    """
    start = time.time()
    while True:
        try:
            if time.time() - start > 10:
                raise Exception(f"Something is wrong. Timeout waiting for port {port}")
            with socket.create_connection(('127.0.0.1', port), timeout=5) as s:
                time.sleep(0.5)
                return
        except socket.error:
            pass
        except socket.timeout:
            raise

@pytest.fixture(scope="session")
def redis_url():
    """
    Starts up the redis server, returns a connection string.
    """
    port = 6380
    db = 9
    
    p = subprocess.Popen(f"redis-server --port {port}".split())
    
    wait_for_port(port)
    
    redis_url = f"redis://127.0.0.1:{port}/{db}"
    
    con = redis.StrictRedis.from_url(redis_url)
    con.flushdb()
    
    yield redis_url
    
    p.terminate()
    
@pytest.fixture(scope="module")
def normal_app(redis_url):
    """
    Run a single-threaded, non-failing server - patched so it doesn't actually
    hit any remote services.
    """
    
    port = 8213
    
    p = subprocess.Popen(f"python {module_dir}/server.py -r {redis_url} -p {port} normal".split())
    wait_for_port(port)
    yield f"http://127.0.0.1:{port}"
    p.terminate()
    
@pytest.fixture(scope="module")
def failing_app(redis_url):
    """
    Run a single-threaded server, patched so it doesn't actually
    hit any remote services, that will intermittently have the depending service
    fail.
    """
    
    port = 9234
    
    p = subprocess.Popen(f"python {module_dir}/server.py -l debug -e 10 -r {redis_url} -p {port} failing".split())
    wait_for_port(port)
    yield f"http://127.0.0.1:{port}"
    p.terminate()
    
    
@pytest.fixture
def conn_with_preload_data(redis_url):
    """
    Preload redis with some data.
    
    Creates 10 unfailing entries (func-test:test1 thru func-test:test10)
    
    And 10 entires that have varying levels of failure (logarithmic scale):
    
        func-test:ftest1, 0
        func-test:ftest2, 1
        func-test:ftest3, 1
        func-test:ftest4, 1
        func-test:ftest5, 2
        func-test:ftest6, 2
        func-test:ftest7, 2
        func-test:ftest8, 2
        func-test:ftest9, 2
        func-test:ftest10, 2
    
    All entries are given a TTL of 20 seconds.
    """
    connection = redis.StrictRedis.from_url(redis_url)
    
    checkin = time.time()
    
    for i in range(1, 11):
        connection.hmset(f"{PREFIX}test{i}", {
            'failures': 0,
            'checkin': checkin,
            'status': STATUS_CLOSED
        })
        connection.hmset(f"{PREFIX}ftest{i}", {
            'failures': round(math.log(i, 2)),
            'checkin': checkin,
            'status': STATUS_OPEN
        })
        connection.expire(f"{PREFIX}ftest{i}", 20)
        connection.expire(f"{PREFIX}test{i}", 20)
        
    yield connection, checkin
    
    connection.flushdb()