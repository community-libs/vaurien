
.. _handlers:

Handlers
========

Vaurien provides a collections of handlers.

blackout
--------

Just closes the client socket on every call.

delay
-----

Adds a delay before the backend is called.

    The delay can happen *after* or *before* the backend is called.


Options:

- **before**: If True adds before the backend is called. Otherwise after (bool, default: True)
- **sleep**: Delay in seconds (int, default: 1)


dummy
-----

