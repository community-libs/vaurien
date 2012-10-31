.. _apis:

APIs
====


**GET** **/handler**

   Returns the current handler in use.

   Example::

      $ curl http://localhost:8080/handler
      normal


**POST** **/handler**

   Set the handler.

   Example::

     $ curl -d"delay" http://localhost:8080/handler
     OK


**GET** **/handlers**

   Returns a list of handlers that are possible to use

   Example::

      $ curl http://localhost:8080/handlers
      {"handlers": ["delay", "error", "hang", "blackout", "dummy"]}


Command line
============

You can use these APIs directly from the command-line using the `vaurienctl`
cli tool.

With it, you can either list the available handlers, get the current one or set
the handler to another one. Here is a quick demo::

    $ vaurienctl list-handlers
    delay, error, hang, blackout, dummy
    $ vaurienctl set-handler blackout
    Handler changed to "blackout"
    $ vaurienctl get-handler
    blackout

