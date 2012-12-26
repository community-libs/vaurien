.. _extending:

Extending Vaurien
=================


You can extend Vaurien by writing new **protocols** or new **behaviors**.


Writing Protocols
-----------------

Writing a new protocol is done by creating a class that inherits from
the :class:`vaurien.protocols.base.BaseProtocol` class.

The class needs to provide three elements:

- a **name** class attribute, the protocol will ne known under that
  name.

- an optional **options** class attribute - a mapping containing options
  for the protocol. Each option value is composed of a
  description, a type and a default value. The mapping is wired in the
  command-line when you run vaurien - and is also used to generate
  the protocol documentation.

- a **_handle** method, that will be called everytime some data
  is ready to be read on the proxy socket or on the backend socket.


The :class:`vaurien.protocols.base.BaseProtocol` class also provides
a few helpers to work with the sockets:

- *_get_data*: a method to read data in a socket. Catches
  *EWOULDBLOCK* and *EAGAIN* errors and loops until they happen.
- *option*: a method to get the value of an option


Example::

    class TCP(BaseProtocol):
        name = 'tcp'
        options = {'reuse_socket': ("If True, the socket is reused.",
                                    bool, False),
                   'buffer': ("Buffer size", int, 8124),
                   'keep_alive': ("Keep the connection alive", bool, False)}

        def _handle(self, source, dest, to_backend):
            # default TCP behavior
            data = self._get_data(source)
            if data:
                dest.sendall(data)
                if not self.option('keep_alive'):
                    data = ''
                    while True:
                        data = self._get_data(dest)
                        if data == '':
                            break
                        source.sendall(data)

                    if not self.option('reuse_socket'):
                        dest.close()
                        dest._closed = True
                    return False
            return data != ''


Once the protocol class is ready, it can be registered via the :class:`Protocol` class::

    from vaurien.protocols import Protocol
    Protocol.register(TPC)


Writing Behaviors
-----------------

Creating new behaviors is very similar to creating protocols.

XXX


Using your protocols and behaviors
----------------------------------

XXX
