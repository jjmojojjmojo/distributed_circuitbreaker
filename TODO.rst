====
TODO
====

Items and new features for consideration or cleanup that needs to be done.

.. contents::

Considerations
==============
These items are high concept ideas that are not, at present, clear goals or tasks. They are also often high risk.

Add Sphinx Tags To Docstrings
-----------------------------
It might be useful to generate API docs using sphinx and `autodoc <http://www.sphinx-doc.org/en/master/usage/quickstart.html#autodoc>`__.

This requires adding markup to the docstrings in the text. 

Rename 'subject' to 'service' in ``CircuitBreaker``
---------------------------------------------------
'subject' is used to refer to the callable object that the ``CircuitBreaker`` class is protecting. It may be more useful to refer to it as the "service".

Rename 'key' to 'name' in ``CircuitBreaker``
--------------------------------------------
It's a bit confusing to use the word 'key' in the parameters. Something more descriptive, that separates what the name is (an identifier for the service) from how it's stored by a given driver would be ideal.

Move 'expires' Concept To ``CircuitBreaker``
--------------------------------------------
Currently the "expires" configuration defines the window within failures "matter". If we have a window of 100 seconds, and the number of failures that is considered a fault condition is 50, we have to hit 50 failures in 100 seconds. When 100 seconds have elapsed, the failure count is reset.

The code relies on the back-end to handle this through the idea of "expiration", influenced by the redis EXPIRE command. The expiration is set to, in this example, 100 seconds *from object creation in the database*.

It may be prudent to refactor things such that two time intervals are tracked in the main CircuitBreaker class: the time since the object was first created (what we currently call "expires", and the time since the object transitioned into the ``STATUS_OPEN`` state (what we currently call ``checkin``).

This way the breaker can decide when the window has closed. The name of the properties could be changed to be more descriptive (something like ``failure_window`` and ``time_since_fault``).

Reset Expires When Breaker Closes
---------------------------------
It seems reasonable that the expiry window should reset when the breaker returns to the ``STATUS_CLOSED`` state. Currently, this only happens when the breaker is unable to load an existing record from the driver and creates a new object. This means that a breaker could naturally close, and then subsequently expire.

It's not clear if this is an issue, however - the current implementation treats "expiry" to mean that the object is deleted from the back-end storage. It is then re-created. This may be unnecessary overhead, especially if the back-end doesn't support automated expiry like redis does.

Features
========

.. warning::
    
    This section contains brain-storming and grand ambitions. No commitments are being made, the author just wants to track ideas as they come up. Status of each will be updated as they are considered and explored. If you like a particular item, reach out!
    
    
Exponential Back-Off
--------------------
The timeout/recheck logic in the current implementation is quite naive. When the breaker is open, the code simply waits for ``timeout`` seconds and 

Implementation: Memcached
-------------------------
A useful Driver implementation would be one using memcached.

Implemetation: Relational DB
----------------------------
A driver implementation using a relational database would be an interesting project to prove out the ``Driver`` API and separation of concerns between the ``Driver`` and ``CircuitBreaker`` classes.

Feature: Status Dashboard
-------------------------
It would be useful to provide, at a minimum, an API for reviewing and managing service data. This could be fleshed out into a web application or RESTful service to integrate into management consoles.