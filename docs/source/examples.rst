.. _examples:


Examples
========


Proxying on an HTTP backend and sending back 50x errors 20% of the time::

    $ vaurien --proxy 0.0.0.0:8888 --backend blog.ziade.org:80 --behavior 20:error --handlers.error.http=1


Adding a 1 second delay on every call to a MySQL server::

    $ vaurien --proxy 0.0.0.0:3307 --backend 0.0.0.0:3306 --stay-connected --behavior 100:delay \
        --handlers.delay.sleep=1


