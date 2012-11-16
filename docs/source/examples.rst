.. _examples:


Examples
========


Proxying on an HTTP backend and sending back 50x errors 20% of the time::

    $ vaurien --protocol http --proxy 0.0.0.0:8888 --backend blog.ziade.org:80 \
            --behavior 20:error


A SSL SMTP proxy with a 5% error rate and 10% delays::

    $ bin/vaurien --proxy 0.0.0.0:6565 --backend mail.messagingengine.com:465 \
            --protocol smtp --behavior 5:error,10:delay


Adding a 1 second delay on **every** call to a MySQL server::

    $ vaurien --proxy 0.0.0.0:3307 --backend 0.0.0.0:3306 --stay-connected --behavior 100:delay \
        --handler-delay-sleep 1


