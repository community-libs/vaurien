Vaurien, the Chaos TCP Proxy
############################

Ever heard of the `Chaos Monkey <http://www.codinghorror.com/blog/2011/04/working-with-the-chaos-monkey.html>`_?

.. image:: monkey.png
    :align: right

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

You can install Vaurien directly from PyPI. The best way to do so is via
`pip`::

    $ pip install vaurien


Design
======

Vaurien is a TCP proxy that simply reads data sent to it and pass it to a
backend, and vice-versa.

It has built-in **protocols**: TCP, HTTP, Redis & Memcache. The **TCP** protocol
is the default one and just sucks data on both sides and pass it along.

Having higher-level protocols is mandatory in some cases, when Vaurien needs to
read a specific amount of data in the sockets, or when you need to be aware
of the kind of response you're waiting for, and so on.

Vaurien also has **behaviors**. A behavior is a class that's going to be
invoked everytime Vaurien proxies a request. That's how you can impact the
behavior of the proxy. For instance, adding a delay or degrading the response
can be implemented in a behavior.

Both **protocols** and **behaviors** are plugins, allowing you to extend Vaurien
by adding new ones.

Last (but not least), Vaurien provides a couple of APIs you can use to
change the behavior of the proxy live. That's handy when you are doing
functional tests against your server: you can for instance start to add
big delays and see how your web application reacts.


Using Vaurien from the command-line
===================================

Vaurien is a command-line tool.

Let's say you want to add a delay for 20% of the HTTP requests made on
**google.com**::

    $ vaurien --protocol http --proxy localhost:8000 --backend google.com:80 \
            --behavior 20:delay


With this set up, Vaurien will stream all the traffic to **google.com** by using
the *http* protocol, and will add delays 20% of the time.

You can find a description of all built-in protocols here: :ref:`protocols`.

You can pass options to the behavior using *--behavior-NAME-OPTION* options::

    $ vaurien --protocol http --proxy localhost:8000 --backend google.com:80 \
        --behavior 20:delay \
        --behavior-delay-sleep 2


Passing all options through the command-line can be tedious, so you can
also create an *ini* file for this::

    [vaurien]
    backend = google.com:80
    proxy = localhost:8000
    protocol = http
    behavior = 20:delay

    [behavior:delay]
    sleep = 2


You can find a description of all built-in behaviors here: :ref:`behaviors`.

You can also find some usage examples here: :ref:`examples`.


Controlling Vaurien live
========================


Vaurien provides an HTTP server with an API, which can be used to control
the proxy and change its behavior on the fly.

To activate it, use the `--http` option::

    $ vaurien --http

By default the server runs on **locahost:8080** but you can change it with
the **--http-host** and **--http-port** options.

See :ref:`apis` for a full list of APIs.


Controlling Vaurien from your code
==================================

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

            with client.with_behavior('error', **options):
                # do something...
                pass

            # we're back to normal here


In this test, the proxy is started and stopped before and after the
test, and the Client class will let you drive its behavior.

Within the **with** block, the proxy will error out any call by using
the *errors* behavior, so you can verify that your application is
behaving as expected when it happens.


Extending Vaurien
=================

Vaurien comes with a handful of useful :ref:`behaviors` and :ref:`protocols`,
but you can create your own ones and plug them in a configuration file.

In fact, that's the best way to create realistic issues: imagine you
have a very specific type of error on your LDAP server everytime your
infrastructure is under heavy load. You can reproduce this issue in your
behavior and make sure your web application behaves as it should.

Creating new behaviors and protocols is done by implementing classes with
specific signatures.

For example if you want to create a "*super*" behavior, you just have
to write a class with two special methods: **on_before_handle** and
**on_after_handle**.

Once the class is ready, you can register it with **Behavior.register**::

    from vaurien.behaviors import Behavior

    class MySuperBehavior(object):

        name = 'super'
        options = {}

        def on_before_handle(self, protocol, source, dest, to_backend):
            # do something here
            return True

         def on_after_handle(self, protocol, source, dest, to_backend):
            # do something else
            return True

    Behavior.register(MySuperBehavior)


You will find a full tutorial in :ref:`extending`.


Contribute
==========

The code repository & bug tracker are located at
https://github.com/mozilla-services/vaurien

Don't hesitate to send us pull requests or open issues!


More documentation
==================

And there is more! Have a look at the other sections of the documentation:

.. toctree::
   :maxdepth: 2

   behaviors
   protocols
   apis
   extending
   examples

