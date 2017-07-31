.. DO NOT EDIT: THIS FILE IS GENERATED AUTOMATICALLY
.. _behaviors:

Behaviors
=========

Vaurien provides a collections of behaviors, all of them are listed on this
page.  You can also write your own behaviors if you need. Have a look at
:ref:`extending` to learn more.



abort
-----

Simulate an aborted connection by a client before receiving a response.

blackout
--------

Immediately closes client socket, no other actions taken.


delay
-----

Adds a delay before or after the backend is called.

The delay can happen *after* or *before* the backend is called.


Options:

- **before**: If True adds before the backend is called. Otherwise after (bool, default: True)
- **sleep**: Delay in seconds (float) (float, default: 1)


dummy
-----

Transparent behavior. Nothing's done.

error
-----

Reads the packets that have been sent then send back "errors".

Used in cunjunction with the HTTP Procotol, it will randomly send back
a 501, 502 or 503.

For other protocols, it returns random data.

The *inject* option can be used to inject data within valid data received
from the backend. The Warmup option can be used to deactivate the random
data injection for a number of calls. This is useful if you need the
communication to settle in some speficic protocols before the random
data is injected.

The *inject* option is deactivated when the *http* protocol is used.


Options:

- **inject**: Inject errors inside valid data (bool, default: False)
- **warmup**: Number of calls before erroring out (int, default: 0)


hang
----

Reads the packets that have been sent then hangs.

Acts like a *pdb.set_trace()* you'd forgot in your code ;)

transient
---------

No documentation. Boooo!


Options:

- **agitate**: Number of calls before succeeding (int, default: 1)
- **inject**: Inject errors inside valid data (bool, default: False)
- **warmup**: Number of calls before erroring out (int, default: 0)



