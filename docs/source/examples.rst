.. _examples:


Examples
========


Proxying on an HTTP backend and sending back 50x errors 20% of the time::

    $ vaurien --protocol http --proxy 0.0.0.0:8888 --backend blog.ziade.org:80 \
              --behavior 20:error


An SSL SMTP proxy with a 5% error rate and 10% delays::

    $ vaurien --proxy 0.0.0.0:6565 --backend mail.example.com:465 \
              --protocol smtp --behavior 5:error,10:delay

An SSL SMTP Proxy that starts to error out after 12 calls (so in the middle of
the transaction)::

    $ vaurien --proxy 0.0.0.0:6565 --backend mail.example.com:465 \
              --protocol smtp --behavior 100:error --behavior-error-warmup 12


Adding a 1 second delay on **every** call to a MySQL server::

    $ vaurien --proxy 0.0.0.0:3307 --backend 0.0.0.0:3306 --stay-connected --behavior 100:delay \
              --behavior-delay-sleep 1


A quick'n'dirty SSH tunnel from your box to another box::

    $ vaurien --stay-connected --proxy 0.0.0.0:8887 --backend 192.168.1.276:22 \
        --protocol-tcp-keep-alive
