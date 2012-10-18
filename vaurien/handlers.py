import gevent


def normal(source, dest, to_backend, name, settings, proxy):
    """Dummy handler
    """
    request = proxy.get_data(source)
    dest.sendall(request)


def delay(source, dest, to_backend, name, settings, proxy):
    """Adds a delay before the backend is called.

    Options:
        - **sleep** : delay in seconds. defaults to 1.
    """
    if to_backend:
        # a bit of delay before calling the backend
        gevent.sleep(settings.get('sleep', 1))

    normal(source, dest, to_backend, name, settings, proxy)


def errors(source, dest, to_backend, name, settings, proxy):
    """Reads the packets that have been sent then throws errors on the socket.
    """
    if to_backend:
        proxy.get_data(source)
        # XXX find how to handle errors (which errors should we send)
        #
        # depends on the protocol
        dest.sendall("YEAH")


def hang(source, dest, to_backend, name, settings, proxy):
    """Reads the packets that have been sent then hangs.
    """
    # consume the socket and hang
    proxy.get_data(source)
    while True:
        gevent.sleep(1.)


def blackout(source, dest, to_backend, name, settings, proxy):
    """Don't do anything -- the sockets get closed
    """
    return


handlers = {'normal': normal,
            'delay': delay,
            'errors': errors,
            'hang': hang,
            'blackout': blackout}
