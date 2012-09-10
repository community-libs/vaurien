Vaurien
#######

THIS IS CURRENTLY BETA AND WILL KILL KITTENS. TAKE CARE.

The idea behind Vaurien is to have a TCP proxy which sometimes drops
packets, sometimes delays requests and sometimes just work.

This is useful to test that applications are able to handle these errors which
will probably happen when in production.

Using vaurien
=============

Vaurien is a command-line tool, here is how you can tell it to proxy google.com
and to delay 20% of the requests::

    $ vaurien --local localhost:8000 --distant google.com:80 --behavior 20:delay

You can also do that with a .ini file, with this in it::

    [vaurien]
    distant = google.com:80
    local = localhost:8000
    behavior = 20:delay

    [handler:delay]
    sleep = 2

As you've seen, it's possible to add configuration for a specific handler.

Extending vaurien
=================

It's also possible to extend vaurien. To do that, you can do the following, in
your configuration file::

    [vaurien]
    behavior = 20:foobar

    [handler:foobar]
    callable = path.to.the.callable
    foo=bar

Your callable needs the following signature::

    def super_callable(source, dest, to_backend, name, settings, server):
        pass

Where source and dest are the source and destination sockets, to_backend is a
boolean that tels you if this is the communication to the proxied server or
from it, name is the name of the callable, settings the settings for *this*
callable and server the server instance (can be useful to look at the global
settings for instance, and other utilities)

Controlling vaurien from a web interface
========================================

Sometimes, it is useful to control how the proxy behaves, on a request to
request basis. Vaurien provides two proxies, the Random one that we defined
earlier and the OnTheFly one.

The "on the fly" proxy comes with a simple http server to control itself. It
has two resources that could be useful to you:

    * `/handler [GET, POST]` which allows to either know what is the current
      handler in use (when doing a `GET`) or to set a new one for the next
      calls (`POST`). You can for instance do this with the following curl
      call::
      
         $ curl -d"delay" http://localhost:8080/handler -H "Content-Type: text/plain"
         OK
            
    * `/handlers [GET]` returns a list of handlers that are possible to use::

        $ curl http://localhost:8080/handlers -H "Content-Type: application/json"
        {"handlers": ["delay", "errors", "hang", "blackout", "normal"]}

You can run the vaurien REST interface by specifying the HTTP flag to it, like
this::

    $ vaurien --http
