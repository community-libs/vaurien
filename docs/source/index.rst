Welcome to Vaurien's documentation!
===================================

*Vaurien, the Chaos TCP Proxy*

Ever heard of the the `Chaos Monkey <http://www.codinghorror.com/blog/2011/04/working-with-the-chaos-monkey.html>` ?

It's a project at Netflix to enhance the infrastructure tolerance. The Chaos Monkey
will randomly shut down some servers or block some network connections, and the system
is supposed to survive to these events. It's a way to verify the high availability
and tolerance of the system.

Besides a redundant infrastructure, if you think about reliability at the level
of you web applications there are many questions that often remain unanswered:

- what happens if the MYSQL server is restarted ? are your connectors able
  to survive this event and continue to work properly afterwards ?

- is your web application still work in degraded mode when Membase is down ?

- are you sending back the right 503s when postgresql times out ?


Of course you can -- and should try out all these scenarios on stage while
your application is getting a realistic load.

But testing these scenarios while you are building your code is a good idea,
and having automated functional tests for this is preferable.

That's where **Vaurien** is useful.

Vaurien is basically a Chaos Monkey for your TCP connections. Vaurien
acts as a proxy between your application and any backend.

You can use it in your functional tests or even on a real deployment
through the command-line.


Using Vaurien from the command-line
===================================

Vaurien is a command-line tool.

Let's say you want to add a delay for 20% of the requests done on google.com::

    $ vaurien --local localhost:8000 --distant google.com:80 --behavior 20:delay


Vaurien will stream all the traffic to google.com but will add delays 20% of the
time.

You can also create a *ini* file for this::

    [vaurien]
    distant = google.com:80
    local = localhost:8000
    behavior = 20:delay

    [handler:delay]
    sleep = 2


And of course you can tweak the behavior of the proxy. Here, we're defining
that the delay will last for 2 seconds.

Each behavior applied on the request or response going through Vaurien
is called a **handler**.


Controlling Vaurien live
========================

Sometimes, it is useful to control how the proxy behaves, on a request to
request basis.

Vaurien provides an HTTP server with 3 APIs that can be used to control the proxy
behavior.

To activate it, use the --http option::

    $ vaurien --http

By default the server runs on port **8080** while the proxy runs on **8000**


Using Vaurien from the code
===========================

If you want to run and drive a Vaurien proxy from your code, the project
provides a few helpers for this.

For example, if you want to write a test that uses a Vaurien proxy,
you can write::


    import unittest
    from vaurien import Client, start_proxy, stop_proxy


    class MyTest(unittest.TestCase):

        def setUp(self):
            self.proxy_pid = start_proxy(port=8080)

        def tearDown(self):
            stop_proxy(self.proxy_pid)


        def test_one(self):
            client = Client()

            with client.with_handler('errors'):
                # do something...


            # we're back to normal here


In this test, the proxy is started and stopped before and after the
test, and the Client class will let you drive its behavior.

During the **with** block, the proxy will error out any call by using
the *errors** hanlder, so you can verify that your application is
behaving as expected when it happens.


Extending vaurien
=================

Vaurien comes with a handful of useful handlers, but you can create your own
handlers and plug them in a configuration file.

In fact that's the best way to create realistic issues: imagine that you
have a very specific type of error on your LDAP server everytime your
infrastructure is under heavy load. You can reproduce this issue in your
handler and make sure your web application behaves as it should.

Creating new handlers is done by implementing a callable with the
following signature::

    def super_callable(source, dest, to_backend, name, settings, server):
        pass


Where:

- **source* and **dest** are the source and destination sockets.
- **to_backend** is a boolean that tels you if this is the communication to
  the proxied server or from it.
- **name** is the name of the callable.
- **settings** the settings for *this* callable
- **server** the server instance - it can be useful to look at the global
  settings for instance, and other utilities.


*to_backend* will let you impact the behavior of the proxy when data is coming
in **or** out of the proxy.

You can then hook it by using the **callable** option::

    [vaurien]
    behavior = 20:foobar

    [handler:foobar]
    callable = path.to.the.callable
    foo=bar


More documentation
==================

Contents:

.. toctree::
   :maxdepth: 2

   apis


