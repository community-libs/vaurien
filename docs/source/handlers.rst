
.. _handlers:

Handlers
========

Vaurien provides a collections of handlers:

- **normal**: transparent proxy.
- **delay**: Adds a delay before the backend is called
- **errors**: Reads the packets that have been sent then throws errors on
  the socket.
- **hang**: Reads the packets that have been sent then hangs.
- **blackout**: Don't do anything -- the sockets get closed
