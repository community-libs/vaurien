import gevent


def normal(source, dest, to_backend, name, settings, server):
    dest.sendall(server.get_data(source))


def delay(**kwargs):
    gevent.sleep(kwargs['settings'].get('sleep', 1))
    normal(**kwargs)


def errors(source, dest, to_backend, name, settings, server):
    """Throw errors on the socket"""
    server.get_data(source)
    # XXX find how to handle errors (which errors should we send)
    dest.sendall("YEAH")


def blackout(source, dest, to_backend, name, settings, server):
    """just drop the packets that had been sent"""
    # consume the socket. That's it.
    server.get_data(source)
