.. DO NOT EDIT: THIS FILE IS GENERATED AUTOMATICALLY
.. _protocols:

Protocols
=========

Vaurien provides a collections of protocols, which are all listed on this page.
You can also write your own protocols if you need. Have a look at
:ref:`extending` to learn more.



http
----

HTTP protocol.


Options:

- **buffer**: Buffer size (int, default: 8124)
- **keep_alive**: Keep the connection alive (bool, default: False)
- **overwrite_host_header**: If True, the HTTP Host header will be rewritten with backend address. (bool, default: False)
- **reuse_socket**: If True, the socket is reused. (bool, default: False)


memcache
--------

Memcache protocol.


Options:

- **buffer**: Buffer size (int, default: 8124)
- **keep_alive**: Keep the connection alive (bool, default: False)
- **reuse_socket**: If True, the socket is reused. (bool, default: False)


mysql
-----

No documentation. Boooo!


Options:

- **buffer**: Buffer size (int, default: 8124)
- **reuse_socket**: If True, the socket is reused. (bool, default: False)


redis
-----

Redis protocol.


Options:

- **buffer**: Buffer size (int, default: 8124)
- **keep_alive**: Keep the connection alive (bool, default: False)
- **reuse_socket**: If True, the socket is reused. (bool, default: False)


smtp
----

SMTP Protocol.



Options:

- **buffer**: Buffer size (int, default: 8124)
- **reuse_socket**: If True, the socket is reused. (bool, default: False)


tcp
---

TCP handler.


Options:

- **buffer**: Buffer size (int, default: 8124)
- **keep_alive**: Keep the connection alive (bool, default: False)
- **reuse_socket**: If True, the socket is reused. (bool, default: False)



