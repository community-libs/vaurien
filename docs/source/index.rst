Welcome to Vaurien's documentation!
===================================

*Vaurien, the Chaos TCP Proxy*

Ever heard of the `Chaos Monkey <http://www.codinghorror.com/blog/2011/04/working-with-the-chaos-monkey.html>`_?

It's a project at Netflix to enhance the infrastructure tolerance. The Chaos Monkey
will randomly shut down some servers or block some network connections, and the system
is supposed to survive to these events. It's a way to verify the high availability
and tolerance of the system.

Besides a redundant infrastructure, if you think about reliability at the level
of your web applications there are many questions that often remain unanswered:

- What happens if the MYSQL server is restarted? Are your connectors able
  to survive this event and continue to work properly afterwards?

- Is your web application still working in degraded mode when Membase is
  down?

- Are you sending back the right 503s when postgresql times out ?


Of course you can -- and should -- try out all these scenarios on stage while
your application is getting a realistic load.

But testing these scenarios while you are building your code is also a good
practice, and having automated functional tests for this is preferable.

That's where **Vaurien** is useful.

Vaurien is basically a Chaos Monkey for your TCP connections. Vaurien
acts as a proxy between your application and any backend.

You can use it in your functional tests or even on a real deployment
through the command-line.


Installing Vaurien
==================

You can install Vaurien directly from PyPI; the best way to do so is via
`pip`::

    $ pip install vaurien


Using Vaurien from the command-line
===================================

Vaurien is a command-line tool.

Let's say you want to add a delay for 20% of the requests done on google.com::

    $ vaurien --proxy localhost:8000 --backend google.com:80 --behavior 20:delay


Vaurien will stream all the traffic to google.com but will add delays 20% of the
time. You can pass options to the handler using *--handler-NAME-OPTION* options::

    $ vaurien --proxy localhost:8000 --backend google.com:80 --behavior 20:delay \
        --handler-delay-sleep 2

Passing all options through the command-line can be tedious, so you can
also create a *ini* file for this::

    [vaurien]
    backend = google.com:80
    proxy = localhost:8000
    behavior = 20:delay

    [handler:delay]
    sleep = 2


Each behavior applied on the request or response going through Vaurien
is called a **handler**, and the ini file gets one section per handler.

You can find a descriptions of all built-in handlers here: :ref:`handlers`.

You can also find some examples here: :ref:`examples`.


Controlling Vaurien live
========================

Sometimes, it is useful to control live the proxy, so you can change its
behavior live between client calls.

Vaurien provides an HTTP server with a few APIs, which can be used to control
the proxy.

To activate it, use the `--http` option::

    $ vaurien --http

By default the server runs on port **8080** while the proxy runs on **8000**

Once it runs, you can call it using cURL or any HTTP client. See the
:ref:`apis`.


Controlling Vaurien in your code
================================

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
            options = {'inject': True}

            with client.with_handler('error', **options):
                # do something...
                pass

            # we're back to normal here


In this test, the proxy is started and stopped before and after the
test, and the Client class will let you drive its behavior.

Within the **with** block, the proxy will error out any call by using
the *errors* handler, so you can verify that your application is
behaving as expected when it happens.


Extending Vaurien
=================

Vaurien comes with a handful of useful :ref:`handlers`, but you can create your own
handlers and plug them in a configuration file.

In fact that's the best way to create realistic issues. Imagine that you
have a very specific type of error on your LDAP server everytime your
infrastructure is under heavy load. You can reproduce this issue in your
handler and make sure your web application behaves as it should.

Creating new handlers is done by implementing a class with a specific signature.

You just have to write a class with a **__call__** method, and register it with
**Handler.register**::

    from vaurien.handlers import Handler

    class MySuperHandler(object):

        name = 'super'
        options = {}

        def __call__(self, client_sock, backend_sock, to_backend):
            # do something here
            return True

    Handler.register(MySuperHandler)


More about this in :ref:`extending`.


Code repository
===============

If you're interested to look at the code, it's there:
https://github.com/mozilla-services/vaurien

Don't hesitate to send us pull requests or to open issues!

More documentation
==================

Contents:

.. toctree::
   :maxdepth: 2

   apis
   handlers
   extending
   keepalive
   examples

