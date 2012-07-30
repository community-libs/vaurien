import gevent
from morveux.util import get_data


def normal(source, dest, settings, back):
    dest.sendall(get_data(source))


def delay(source, dest, settings, back):
    gevent.sleep(settings['sleep'])
    normal(source, dest)


def errors(source, dest, settings, back):
    """Throw errors on the socket"""
    get_data(source)  # don't do anything with the data
    # XXX find how to handle errors (which errors should we send)
    dest.sendall("YEAH")


def blackout(source, dest, settings, back):
    """just drop the packets that had been sent"""
    # consume the socket. That's it.
    get_data(source)
