import os
import gevent



class BaseHandler(object):

    options = {}
    name = ''

    def _get_data(self, sock, buffer=1024):
        data = sock.recv(1024)
        if not data:
            sock.close()
            return
        return data


class Dummy(BaseHandler):
    name = 'dummy'
    options = {}

    def __call__(self, source, dest, to_backend, name, settings, proxy):
        """Dummy handler
        """
        data = self._get_data(source)
        if data:
            dest.sendall(data)


class Delay(Dummy):
    name = 'delay'
    options = {}

    def __call__(self, source, dest, to_backend, name, settings, proxy):
        """Adds a delay before the backend is called.

        Options:
            - **sleep** : delay in seconds. defaults to 1.
        """
        if to_backend:
            # a bit of delay before calling the backend
            gevent.sleep(settings.get('sleep', 1))

        super(Delay, self)(source, dest, to_backend, name, settings, proxy)


class Error(BaseHandler):
    name = 'error'
    options = {}

    def __call__(self, source, dest, to_backend, name, settings, proxy):
        """Reads the packets that have been sent then throws errors on the socket.
        """
        data = self._get_data(source)

        if to_backend:
            # XXX find how to handle errors (which errors should we send)
            # depends on the protocol
            source.sendall(os.urandom(1000))
        source.close()
        dest.close()


class Hang(BaseHandler):
    name = 'hang'
    options = {}

    def ___call__(self, source, dest, to_backend, name, settings, proxy):
        """Reads the packets that have been sent then hangs.
        """
        # consume the socket and hang
        data = self._get_data(source)
        while data:
            data = self._get_data(source)

        while True:
            gevent.sleep(1.)


class Blackout(BaseHandler):
    name = 'hang'
    options = {}

    def __call__(self, source, dest, to_backend, name, settings, proxy):
        """Don't do anything -- the sockets get closed
        """
        source.close()
        dest.close()


handlers = {'dummy': Dummy(),
            'delay': Delay(),
            'error': Error(),
            'hang': Hang(),
            'blackout': Blackout()}
