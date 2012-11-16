.. _extending:

Extending Vaurien
=================

.. note::

   Before reading this section, make sure you read :ref:`keep`


You can extend Vaurien by writing new **protocols** or new **behaviors**.


Writing Protocols
-----------------

XXX


Writing Handlers
----------------

Creating new handlers is done by implementing a class with a specific
signature::


    from vaurien.handlers import Handler

    class MySuperHandler(object):

        name = 'super'
        options = {}

        def __call__(self, client_sock, backend_sock, to_backend):
            # do something here
            return True


    Handler.register(MySuperHandler)


Vaurien can use this handler and call it everytime data is being seen on one hand
or the other.

You must call **Handler.register** against your class is order to add it
to the list of the available plugins.

Let's see the different attributes and options we have in this class:

- **name** - the name under which your backend is known
- **options** - a mapping containing your handler options
- **client_sock** - the socket opened with the client
- **backend_sock** - the socket opened with the backend server
- **to_backend** - a boolean giving the direction of the call. If True
  it means some data is available in the client socket, that is supposed
  to go to the backend. If False, it means data is available on the backend
  socket and should be tramsmitted back to the client.

For the handler options, each option is defined in the **options** mapping.
The key is the option name and the value is a 3-tuple providing:

- a description
- a type
- a default value

**every option is optional and need a default value**

Everytime a handler is used, it gets two extra attributes:

- **settings** - the settings loaded for the handler
- **proxy** - the proxy instance

The BaseHandler class
---------------------

XXX

Full handler example
--------------------

Here is how the `delay` handler is specified::

    from vaurien.handlers.base import BaseHandler


    class Dummy(BaseHandler):
        """Dummy handler.

        Every incoming data is passed to the backend with no alteration,
        and vice-versa.
        """
        name = 'dummy'
        options = {'keep_alive': ("Keep-alive protocol",
                                bool, False),
                'reuse_socket': ("If True, the socket is reused.",
                                    bool, False)}

        def __call__(self, client_sock, backend_sock, to_backend):
            data = self._get_data(client_sock, backend_sock, to_backend)
            if data:
                dest = to_backend and backend_sock or client_sock
                source = to_backend and client_sock or backend_sock
                dest.sendall(data)

                # If we are not keeping the connection alive
                # we can suck the answer back and close the socket
                if not self.option('keep_alive'):
                    data = ''
                    while True:
                        data = dest.recv(1024)

                        if data == '':
                            break
                        source.sendall(data)
                    dest.close()
                    dest._closed = True
            elif not to_backend:
                # We want to close the socket if the backend sock is empty
                if not self.option('reuse_socket'):
                    backend_sock.close()
                    backend_sock._closed = True

            return data != ''


Using handlers
--------------

Once the handler is ready, you can point it to Vaurien
by providing its fully qualified name - e.g. the class name prefixed
by the module and package(s) names.

Then you can use it with the **--behavior** option::

    $ vaurien --proxy localhost:8000 --backend google.com:80 \
        --behavior 20:path.to.the.callable \
        --handler-delay-sleep 2

Or by using a configuration file::

    [vaurien]
    behavior = 20:foobar

    [handler:foobar]
    callable = path.to.the.callable
    foo=bar

And calling Vaurien with --config::

    $ vaurien --config config.ini
