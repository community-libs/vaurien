.. _apis:

APIs
====

You can control vaurien from its APIs. There is a REST API and a command-line
API

The REST API
------------

**GET** **/behavior**

   Returns the current behavior in use, as a json object.

   Example::

       $ curl -XGET http://localhost:8080/behavior
       {
         "behavior": "dummy"
       }


**PUT** **/behavior**

   Set the behavior. The behavior must be provided in a JSON object,
   in the body of the request, with a **name** key for the behavior
   name, and any option to pass to the behavior class.

   .. note::

        Don't forget to set the "application/json" Content-Type header
        when doing your calls.

   Example::

      $ curl -XPUT -d '{"sleep": 2, "name": "delay"}' http://localhost:8080/behavior \
             -H "Content-Type: application/json"
       {
         "status": "ok"
       }


**GET** **/behaviors**

   Returns a list of behaviors that are possible to use

   Example::

      $ curl -XGET http://localhost:8080/behaviors
      {
      "behaviors": [
          "blackout",
          "delay",
          "dummy",
          "error",
          "hang"
      ]
      }

If you want to control vaurien from the command-line, you can do so by using
`vaurienclient <http://github.com/mozilla-services/vaurienclient>`_.
`vaurienctl --help` will provide you some help.
