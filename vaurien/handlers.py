import os

import gevent


def _get_data(sock, buffer=1024):
    data = sock.recv(1024)
    if data == '':
        sock.close()
        return
    return data


def normal(source, dest, to_backend, name, settings, proxy):
    """Dummy handler
    """
    data = _get_data(source)

    if data != '':
        dest.sendall(data)


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
    data = _get_data(source)

    if to_backend:
        # XXX find how to handle errors (which errors should we send)
        #
        # depends on the protocol
        source.sendall(os.urandom(1000))

    source.close()
    dest.close()

def hang(source, dest, to_backend, name, settings, proxy):
    """Reads the packets that have been sent then hangs.
    """
    # consume the socket and hang
    data = _get_data(source)
    while data != '':
        data = _get_data(source)

    while True:
        gevent.sleep(1.)


def blackout(source, dest, to_backend, name, settings, proxy):
    """Don't do anything -- the sockets get closed
    """
    source.close()
    dest.close()


handlers = {'normal': normal,
            'delay': delay,
            'errors': errors,
            'hang': hang,
            'blackout': blackout}
