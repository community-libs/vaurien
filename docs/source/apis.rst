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
      {"handlers": ["delay", "errors", "hang", "blackout", "normal"]}

