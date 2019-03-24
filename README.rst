===========================
Distributed Circuit-Breaker
===========================

:author: Josh Johnson <jjmojojjmojo@gmail.com>

.. contents::


Overview
========
This project is a distributed implementation of the "Circuit Breaker Pattern" popularized by Michael Nygard's book, *Release It*.

.. note::
	
	Martin Fowler did a nice `write up about the pattern <https://martinfowler.com/bliki/CircuitBreaker.html>`__ as well.
	


Like an electrical circuit breaker, this project provides a way to prevent faults by preventing access to a back-end system when conditions are not safe. In the case of an electrical circuit breaker, the back-end is the mains power. In the case of this project, the back-end is some sort of volatile service. 

When the breaker is "CLOSED", calls to the service are allowed to proceed.

When the breaker is "OPEN", calls to the service are blocked.

The breaker will transition to the "OPEN" state when a condition is met. In the case of an electrical circuit breaker, that condition is more electrical load than a circuit can handle, due to too many devices plugged into the same circuit, or a fault condition of some kind. 

In the case of this project, the condition is that a given service has returned some sort of error state more than a given number of times within a given time interval.

The circuit breaker code tries to call the service after a set time has elapsed. If it succeeds, the breaker transitions back to the "CLOSED" state, and the result is returned.

For more information on the design, motivation, and interesting walk-through of various parts of the code, refer to my blog post (TBD). 

There are two things that make this implementation (probably) novel:

* It is designed for use in a service-oriented architecture with microservices in mind. As such, it's *distributed*. It uses a central back-end to keep all agents that rely on a given service in sync with regards to its status.
* This implementation has a simple plug-in interface allowing for adaptation to (probably) any sort of back-end.

Installation
============

.. note::
	
	The package is currently in a pre-release state, and as such, is **not** on PyPi. If a 1.0 version ever happens, it'll be released properly and the installation can be as simple as :code:`pip install jjmojojjmojo-circuitbreaker`.
	
This project was developed with Python 3.7. That's the only system-level prerequisite.

After checking out the source repository, the library can be installed via pip::
	
	$ git clone https://github.com/jjmojojjmojo/distributed-circuitbreaker.git
	$ cd distributed-circuitbreaker/
	$ sudo pip install src/jjmojojjmojo_circuitbreaker
	
.. note::
	
	It's preferable that you use a virtual python environment - the process is identical, just initialize your environment and don't use :code:`sudo`.
	
For typical use, you will want to have `redis <https://redis.io/>`__ installed, or access to a redis server.

Usage
=====
To use in your applications, create a callable that handles the remote request and raises an exception (any exception) when the request fails.

There are two available drivers - one is not distributed (:code:`MemoryDriver`), the other uses Redis as a back-end (:code:`RedisDriver`). Drivers are located in the :code:`jjmojojjmojo.circuitbreaker.drivers` package.

There are a few factory functions in :code:`jjmojojjmojo.circutibreaker` that combine driver configuration and breaker configuration into one convenient API, :code:`RedisCircuitBreaker` and :code:`MemoryCircuitBreaker`.

Settings Overview
-----------------
For most use cases, you will only need to consider the following parameters:

:key: A unique name for the service.
:expires: How long should we care about errors?
:timeout: How often should we retry the service once the breaker has opened?
:failures: The number of failures that will constitute a fault.

The breaker will open when the number of failures counted *within the window defined by expires* exceeds the maximum number of :code:`failures`.

Once the breaker is open, it will recheck the service after the :code:`timeout` has expired.

For example, imagine we have a service called *myservice*. We've set the :code:`expires` window to 3600 seconds (1 hour), number of failures to 10, and the :code:`timeout` to 60 seconds.

.. code:: python
    
    from jjmojojjmojo.circuitbreaker import RedisCircuitBreaker
    
    from yourapplication.contrived import service_func
    
    breaker = RedisCircuitBreaker(
        "myservice", 
        service_func, 
        failures=10, 
        timeout=60, 
        redis_url="redis://localhost:6379/0", 
        expires=3600)
    
    # now service_func is protected, and we call breaker to activate it
    print(breaker())
    

Lets say *myservice* fails, on average, 3 times an hour. With this configuration, this will never trip the breaker. The client code will handle the errors as it sees fit (retry, report, alert the user, returned a cached response, etc).

If *myservice* was having some technical difficulty one day, and it went down outright, every request would fail. Assuming it didn't come back up within the one hour window, the breaker in each client would close after the 11th failure. The clients would then get :code:`CircuitBreakerOpen`. This lets the client know something is wrong with the service, and so it can take different action. Every 60 [*]_ seconds, the clients would retry the service and re-open the breaker if it succeeded. 

After one hour, the service window would expire, and the breaker would reset to closed. If the service wasn't back up, the cycle would happen again.

In most cases, catastrophic failures like this aren't common, and the service would be back up within the window. This is the main function of the circuit breaker pattern: it prevents "slamming" a service that is overloaded or otherwise in trouble, allowing for self rectification.

.. [*] Due to *jitter*, the actual timeout is between 60 and 70 seconds. See `Setting The Jitter Function`_ for details and how to override this.

Setting The Jitter Function
---------------------------
To prevent the `thundering herd problem <https://en.wikipedia.org/wiki/Thundering_herd_problem>`__, the :code:`CircuitBreaker` class uses the concept of "jitter", or random variations. Jitter is applied to the :code:`timeout` when deciding if a closed breaker should retry calling the service.

By default, the jitter is a simple random integer between 1 and 10 (see :code:`jjmojojjmojo.circuitbreaker.base.rand_int_jitter()`).

Jitter is useful for adjusting how your clients behave, and will likely need to be tweaked at scale.

Jitter is provided to the :code:`CircuitBreaker` as a callable of some sort. It takes no parameters and is expected to return a simple number (integer, float). That number is added to the :code:`timeout` value when a closed breaker is considering whether it should check in with the service again.

Here is a simple example of switching to a random Guassian distribution (aka `Normal Distribution <https://en.wikipedia.org/wiki/Normal_distribution>`__):

.. code:: python
    
    import random
    from yourapplication.contrived import service_func
    from jjmojojjmojo.circuitbreaker import RedisCircuitBreaker
    
    def guass_jitter():
        """
        Return a simple random jitter value within 1 sigma of 2 in a guassian distribution.
        """
        return random.guass(2, 1)
    
    breaker = RedisCircuitBreaker(
        "myservice", 
        service_func, 
        failures=10, 
        timeout=60, 
        redis_url="redis://localhost:6379/0", 
        expires=3600, 
        jitter=guass_jitter)
    
To *fix* the jitter, such that it will always be the same amount, you can pass a non-callable value.

.. code:: python
    
    ...
    breaker = RedisCircuitBreaker(
        "myservice", 
        service_func, 
        failures=10, 
        timeout=60, 
        redis_url="redis://localhost:6379/0", 
        expires=3600, 
        jitter=0)  # fixed jitter to 0

Example 1: Wrapping random.dog
------------------------------
To illustrate how the circuitbreaker is designed to function, I built a simple wrapper for `David Valachovic's <https://davidvalachovic.com/>`__ `https://random.dog <https://random.dog>`__ web service.

The service itself is really easy to use, we just need to make a GET request to https://random.dog/woof.json. We do this on the server side in the example, but use the :code:`RedisCircutiBreaker` to protect it from too many concurrent failures. There is a single-page web application that talks to the server-side code. It also displays the state of the circuit breaker so you can peek into what's going on.

When an error is detected, a picture of my dog Peanut is displayed, overlayed with the word "ERROR". 

When the breaker is open, the back-end returns a cached response instead.

.. note::
    
    This is just done to provide a difference between an error state and the "breaker open" state. In a real-world application, more useful actions would be taken: return a cached response, a retry by the front-end, etc.
    

The code is located in :code:`examples/random_dog`.

It is heavily commented inline. It uses :code:`IntermittentFailer` to provide a reliable failure rate (random.dog is quite robust).

Before proceeding, activate the virtual environment:

.. code:: console
    
    $ source bin/activate
    (distributed_circuitbreaker) $
    

To use the examples, install the :code:`requirements.txt` in the :code:`examples` directory:

.. code:: console
    
    (distributed_circuitbreaker) $ pip install -r examples/requirements.txt
    
Before you start a web server (`gunicorn <https://gunicorn.org/>`__ is provided), you will need to have a running redis. The example assumes this is running on the default port on your local host. You can start the server thusly:

.. code:: console
    
    $ redis-server
    
Then run the server:

.. code:: console
    
    (distributed_circuitbreaker) $ gunicorn -w4 examples:random_dog
    
The example is configured to use DEBUG level logging output, so you can watch the console and see how things happen as they do.

.. note::
    
    The number of workers you launch will influence the way the example behaves. This is because :code:`IntermittenFailer` is not distributed and a new copy is made for each worker. This makes each worker's fail rate cumulative in regards to the failure count in the circuit breaker. It works out nicely though, since the failures feel a little more random because of how :code:`gunicorn` load balances the workers.
    


Development Setup
=================
A local copy of `redis <https://redis.io/>`__ is required for development (a remote install would work but it's not recommended).

The setup process is straight forward. 

First, clone this repository:

.. code:: console
    
    $ git clone git@github.com:jjmojojjmojo/distributed_circuitbreaker.git
    
Next, initialize and activate the virtual environment:

.. code:: console
    
    $ virtualenv .
    $ source bin/activate
    
Install the prerequesites:

.. code:: console
    
    (distributed-circuitbreaker) $ pip install -r requirements.txt
    
Install the source:

.. code:: console
    
    (distributed-circuitbreaker) $ pip install -e src/jjmojojjmojo_circuitbreaker
    
Logging
=======
The code in this project makes extensive use of the python logging module. To peer deeply into its operation, set the log level to 'DEBUG'.

This can be done globally like this, and controlled via an environment variable. Just add code like the following before your application code is executed (be aware that this will change the *global* logging level, so you'll see debugging messages from any libraries that emit them):

.. code:: python
    
    import logging
    import os
    
    loglevel = os.environ.get("LOGLEVEL", "debug").upper()
    
    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=getattr(logging, loglevel))
    
The format here is designed to mimic `gunicorn's default log formatting <https://github.com/benoitc/gunicorn/blob/29f0394cdd381df176a3df3c25bb3fdd2486a173/gunicorn/glogging.py#L87>`__. You will want to use a format and configuration appropriate for your situation.

.. note::
    
    For complete details, see `python's logging documentation <https://docs.python.org/3/library/logging.html>`__.
    

Running The Tests
=================
Tests are written using `py.test <https://docs.pytest.org/en/latest/index.html>`__.

The unit tests are located in `src/jjmojojjmojo_circuitbreaker/jjmojojjmojo/circuitbreaker/tests`.

The unit tests can be run without any external dependencies:

.. code:: console
    
    (distributed-circuitbreaker) $ pytest src/
    
The functional are located tests require some additional libraries, and `redis-server` on your `$PATH`.

.. warning::
    
    The functional tests **are destructive**. They use a nonstandard port (6380) and database #9 to prevent accidental destruction of useful data, but they do run `FLUSHDB <https://redis.io/commands/flushdb>`__ between sessions.
    

To install the additional libraries, install `func/requirements.txt`:

.. code:: console
    
    (distributed-circuitbreaker) $ pip install -r func/requirements.txt
    
Now you can run all of the tests together:

.. code:: console
    
    (distributed-circuitbreaker) $ pytest src/ func/
    
To generate a coverage report, invoke the `pytest-cov <https://pypi.org/project/pytest-cov/>`__ plugin:

.. code:: console
    
    (distributed-circuitbreaker) $ pytest --cov-report term --cov=jjmojojjmojo.circuitbreaker func src

Multi-Client/Threaded Testing
=============================
`locust.io <https://locust.io/>`__ configuration is provided in the :code:`func` directory for load testing and testing the breaker implementations across multiple processes.

To run a locust swarm against the functional test server:

.. code:: console
    
    $ source bin/activate
    (distributed-circuitbreaker) $ pip install -r func/requirements.txt
    (distributed-circuitbreaker) $ cd func
    (distributed-circuitbreaker) $ locust
    
Then you can open http://127.0.0.1:8089, and stress test away. 

.. note::
    
    The tests don't do much at the moment - it's a quick way to run a lot of gunicorn workers and slam them with requests to see what happens in general terms.
    
Testing Utility Tidbits
=======================
I had some fun working out tests cases for this project. This section points out some code that I found particularly worth noting.

The `IntermittentFailer`
------------------------
To make testing easier, I've built a configurable function that will fail at a predictable rate.

It is located in the `jjmojojjmojo.circuitbreaker.tests.util` module.

The Test Server
---------------
In the `func` directory, I've built a server for functional testing that uses the `IntermittentFailer` class. The module is named `server.py`. It is configured via command-line options, so you can easily stand up a web service that will fail at a predictable rate for integration tests.

TODO Items
==========
A running list of things to consider and/or clean up are tracked in TODO.rst.