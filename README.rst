Vaurien
#######

THIS IS CURRENTLY BETA AND COULD KILL KITTENS. TAKE CARE.

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
