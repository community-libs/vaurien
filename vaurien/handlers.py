import gevent


def normal(source, dest, to_backend, name, settings, server):
    request = server.get_data(source)
    dest.sendall(request)


def delay(source, dest, to_backend, name, settings, server):
    if to_backend:
        # a bit of delay before calling the backend
        gevent.sleep(kwargs['settings'].get('sleep', 1))

    normal(source, dest, to_backend, name, settings, server)


def errors(source, dest, to_backend, name, settings, server):
    """Throw errors on the socket"""
    if to_backend:
        server.get_data(source)
        # XXX find how to handle errors (which errors should we send)
        #
        # depends on the protocol
        dest.sendall("YEAH")


def hang(source, dest, to_backend, name, settings, server):
    """Reads the packets that have been sent."""
    # consume the socket and hang
    server.get_data(source)
    while True:
        gevent.sleep(1.)


def blackout(source, dest, to_backend, name, settings, server):
    """Don't do anything -- the sockets get closed"""
    return
