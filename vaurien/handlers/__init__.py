import os
import gevent


class BaseHandler(object):
    options = {}
    name = ''

    def __init__(self, settings=None):
        if settings is None:
            self.settings = {}
        else:
            self.settings = settings

    def update_settings(self, settings):
        self.settings.update(settings)

    @property
    def option(self, name):
        return self.settings.get(name, options[name][2])

    def _get_data(self, sock, buffer=1024):
        data = sock.recv(1024)
        if not data:
            sock.close()
            return
        return data


class Dummy(BaseHandler):
    """Dummy handler
    """
    name = 'dummy'
    options = {}

    def __call__(self, source, dest, to_backend, name, proxy):
        data = self._get_data(source)
        if data:
            dest.sendall(data)


class Delay(Dummy):
    """Adds a delay before the backend is called.
    """
    name = 'delay'
    options = {'sleep': ("Delay in seconds", int, 1),
               'before':
                    ("If True adds before the backend is called. Otherwise"
                     " after", bool, True)}

    def __call__(self, source, dest, to_backend, name, proxy):
        if to_backend and self.options('before'):
            # a bit of delay before calling the backend
            gevent.sleep(self.options('sleep'))

        super(Delay, self)(source, dest, to_backend, name, proxy)



class Error(BaseHandler):
    """Reads the packets that have been sent then throws errors on the socket.
    """
    name = 'error'
    options = {'inject': ("Inject errors inside valid data", bool, False)}

    def __call__(self, source, dest, to_backend, name, proxy):
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

    def ___call__(self, source, dest, to_backend, name, proxy):
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

    def __call__(self, source, dest, to_backend, name, proxy):
        """Don't do anything -- the sockets get closed
        """
        source.close()
        dest.close()


handlers = {'dummy': Dummy(),
            'delay': Delay(),
            'error': Error(),
            'hang': Hang(),
            'blackout': Blackout()}
