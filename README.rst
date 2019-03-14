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
	
	The package is currently in a pre-release state, and as such, is **not** on PyPi. If a 1.0 version ever happens, it'll be released properly and the installation can be as simple as ``pip install jjmojojjmojo-circuitbreaker``.
	
This project was developed with Python 3.7. That's the only system-level prerequisite.

After checking out the source repository, the library can be installed via pip::
	
	$ git clone https://github.com/jjmojojjmojo/distributed-circuitbreaker.git
	$ cd distributed-circuitbreaker/
	$ sudo pip install src/jjmojojjmojo_circuitbreaker
	
.. note::
	
	It's preferable that you use a virtual python environment - the process is identical, just initialize your environment and don't use ``sudo``.
	
For typical use, you will want to have redis installed, or access to a redis server.

Usage
=====
To use in your applications, create a callable that handles the remote request and raises an exception (any exception) when the request fails.

There are two available drivers - one is not distributed (``MemoryDriver``), the other uses Redis as a back-end (``RedisDriver``). Drivers are located in the ``jjmojojjmojo.circuitbreaker.drivers`` package.

There are a few composition factory classes in ``jjmojojjmojo.circutibreaker`` that combine driver configuration and breaker configuration into one API, ``RedisCircuitBreaker`` and ``MemoryCircuitBreaker``.

Development Setup
=================
A local copy of redis is required for development (a remote install would work but it's not recommended).

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
    
Running The Tests
=================
Tests are written using `py.test <https://docs.pytest.org/en/latest/index.html>`__.

The unit tests are located in `src/jjmojojjmojo_circuitbreaker/jjmojojjmojo/circuitbreaker/tests`.

The unit tests can be run without any external dependencies:

.. code:: console
    
    (distributed-circuitbreaker) $ pytest src/
    
The functional are located tests require some additional libraries, and `redis-server` on your `$PATH`.

To install the additional libraries, install `func/requirements.txt`:

.. code:: console
    
    (distributed-circuitbreaker) $ pip install -r func/requirements.txt
    
Now you can run all of the tests together:

.. code:: console
    
    (distributed-circuitbreaker) $ pytest src/ func/
    
To generate a coverage report, invoke the `pytest-cov <https://pypi.org/project/pytest-cov/>`__ plugin:

.. code:: console
    
    (distributed-circuitbreaker) $ pytest --cov-report term --cov=jjmojojjmojo.circuitbreaker func src

Testing Utility Tidbits
=======================
I had some fun working out tests cases for this project. This section points out some code that I found particularly worth noting.

The `IntermittentFailer`
------------------------
To make testing easier, I've built a configurable function that will fail at a predictable rate.

It is located in the `jjmojojjmojo.circuitbreaker.tests.util` module.

The Test Server
---------------
In the `func` directory, I've built a server for functional testing that uses the `IntermittentFailer` class. The module is named `server.py`. It is configured via command-line options, so you can easily stand up a web service that will fail at a predictable time for integration tests.
