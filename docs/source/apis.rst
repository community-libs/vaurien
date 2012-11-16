.. _apis:

APIs
====


**GET** **/behavior**

   Returns the current behavior in use.

   Example::

       $ curl -XGET http://localhost:8080/behavior
       {
         "behavior": "dummy"
       }


**POST** **/behavior**

   Set the behavior. The behavior must be provided in a JSON mapping
   in the body of the request, with a **name** key for the behavior
   name, and any option to pass to the behavior class.

   Example::

      $ curl -d '{"sleep": 2, "name": "delay"}' http://localhost:8080/behavior \
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


Command line
------------

You can use these APIs directly from the command-line using the **vaurienctl**
CLI tool.

**vaurienctl** can be used to list the available behaviors, get the current one,
or set it.

Here is a quick demo::

    $ vaurienctl list-behaviors
    delay, error, hang, blackout, dummy

    $ vaurienctl set-behavior blackout
    Behavior changed to "blackout"

    $ vaurienctl get-behavior
    blackout
