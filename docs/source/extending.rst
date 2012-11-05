.. _extending:

Writing Handlers
================

Creating new handlers is done by implementing a class with a specific signature.

You can inherit from the base class Vaurien provides and just implement the
**__call__** method::

    from vaurien.handlers import BaseHandler

    class MySuperHandler(BaseHandler):

        name = 'super'
        options = {}

        def __call__(self, client_sock, backend_sock, to_backend):
            # do something here


Vaurien can use this handler and call it everytime data is being seen on one hand
or the other.

Where:

- **name** - the name under which your backend is known
- **options** - a mapping containing your handler options
- **client_sock** - the socket opened with the client
- **backend_sock** - the socket opened with the backend server
- **to_backend** - a boolean giving the direction of the call. If True
  it means some data is available in the client socket, that is supposed
  to go to the backend. If False, it means data is available on the backend
  socket and should be tramsmitted back to the client.

A handler instance is initialized with two values:

- **settings** - the settings loaded for the handler
- **proxy** - the proxy instance

For the handler options, each option is defined in the **options** mapping.
The key is the option name and the value is a 3-tuple providing:

- a description
- a type
- a default value

**every option is optional and need a default value**

Full handler example
--------------------

Here is how the `delay` handler is specified::


    from vaurien.handlers import BaseHandler

    class Delay(BaseHandler):
        """Adds a delay before the backend is called.
        """
        name = 'delay'
        options = {'sleep': ("Delay in seconds", int, 1),
                'before':
                        ("If True adds before the backend is called. Otherwise"
                        " after", bool, True)}

        def __call__(self, client_sock, backend_sock, to_backend):
            before = to_backend and self.options('before')
            after = not to_backend and not self.options('before')

            if before:
                gevent.sleep(self.options('sleep'))

            data = self._get_data(client_sock, backend_sock, to_backend)

            if after:
                gevent.sleep(self.options('sleep'))

            if data:
                dest = to_backend and backend_sock or client_sock
                dest.sendall(data)


Using handlers
--------------

Once the handler is ready, you can point it to Vaurien
by providing its fully qualified name - e.g. the class name prefixed
by the module and package(s) names.

Then you can use it with the **--behavior** option::

    $ vaurien --local localhost:8000 --distant google.com:80 \
        --behavior 20:path.to.the.callable \
        --handlers.delay.sleep 2

Or by using a configuration file::

    [vaurien]
    behavior = 20:foobar

    [handler:foobar]
    callable = path.to.the.callable
    foo=bar

And calling Vaurien with --config::

    $ vaurien --config config.ini
