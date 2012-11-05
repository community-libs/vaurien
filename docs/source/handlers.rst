
.. _handlers:

Handlers
========

Vaurien provides a collections of handlers.

blackout
--------

No documentation. Boooo!

delay
-----

Adds a delay before the backend is called.
    

Options:

- **before**: If True adds before the backend is called. Otherwise after (bool, default: True)
- **sleep**: Delay in seconds (int, default: 1)


dummy
-----

Dummy handler
    
error
-----

Reads the packets that have been sent then throws errors on the socket.
    

Options:

- **inject**: Inject errors inside valid data (bool, default: False)
- **warmup**: Number of calls before erroring out (int, default: 0)


hang
----

No documentation. Boooo!


