import os
import copy
import gevent


class BaseHandler(object):
    options = {}
    name = ''

    def __init__(self, settings=None, proxy=None):
        self.proxy = proxy

        if settings is None:
            self.settings = {}
        else:
            self.settings = copy.copy(settings)

    def update_settings(self, settings):
        self.settings.update(settings)

    def _convert(self, value, type_):
        if type_ == bool:
            value = value.lower()
            return value in ('y', 'yes', '1', 'on')
        return type_(value)

    def option(self, name):
        _, type_, default = self.options[name]
        value = self.settings.get(name, default)
        return self._convert(value, type_)

    def _get_data(self, client_sock, backend_sock, to_backend, buffer=1024):
        sock = to_backend and client_sock or backend_sock
        data = sock.recv(1024)
        if not data:
            sock.close()
            return
        return data


class Dummy(BaseHandler):
    """Dummy handler.

    Every incoming data is passed to the backend with no alteration,
    and vice-versa.
    """
    name = 'dummy'
    options = {}

    def __call__(self, client_sock, backend_sock, to_backend):
        data = self._get_data(client_sock, backend_sock, to_backend)
        if data:
            dest = to_backend and backend_sock or client_sock
            dest.sendall(data)


class Delay(BaseHandler):
    """Adds a delay before the backend is called.

    The delay can happen *after* or *before* the backend is called.
    """
    name = 'delay'
    options = {'sleep': ("Delay in seconds", int, 1),
               'before':
                    ("If True adds before the backend is called. Otherwise"
                     " after", bool, True)}

    def __call__(self, client_sock, backend_sock, to_backend):
        before = to_backend and self.options('before')
        after = not to_backend and not self.options('before')

        if before:
            gevent.sleep(self.options('sleep'))

        data = self._get_data(client_sock, backend_sock, to_backend)

        if after:
            gevent.sleep(self.options('sleep'))

        if data:
            dest = to_backend and backend_sock or client_sock
            dest.sendall(data)


class Error(Dummy):
    """Reads the packets that have been sent then send random data in the socket.

    The *inject* option can be used to inject data within valid data received
    from the backend. The Warmup option can be used to deactivate the random
    data injection for a number of calls. This is useful if you need the
    communication to settle in some speficic protocols before the ramdom
    data is injected.

    """
    name = 'error'
    options = {'inject': ("Inject errors inside valid data", bool, False),
               'warmup': ("Number of calls before erroring out", int, 0)}

    def __init__(self, settings=None, proxy=None):
        super(Error, self).__init__(settings, proxy)
        self.current = 0

    def __call__(self, client_sock, backend_sock, to_backend):
        if self.current < self.option('warmup'):
            self.current += 1
            return super(Error, self).__call__(client_sock, backend_sock, to_backend)

        data = self._get_data(client_sock, backend_sock, to_backend)
        if not data:
            return

        dest = to_backend and backend_sock or client_sock

        if self.option('inject'):
            if not to_backend:      # back to the client
                middle = len(data) / 2
                dest.sendall(data[:middle] + os.urandom(100) + data[middle:])
            else:                   # sending the data tp the backend
                print 'sending data to the backend'
                dest.sendall(data)

        else:
            if not to_backend:
                # XXX find how to handle errors (which errors should we send)
                # depends on the protocol
                dest.sendall(os.urandom(1000))
            else:          # sending the data tp the backend
                dest.sendall(data)


class Hang(BaseHandler):
    """Reads the packets that have been sent then hangs.

    Acts like a *pdb.set_trace()* you'd forgot in your code ;)
    """
    name = 'hang'
    options = {}

    def ___call__(self, client_sock, backend_sock, to_backend):
        # consume the socket and hang
        data = self._get_data(client_sock, backend_sock, to_backend)
        while data:
            data = self._get_data(client_sock, backend_sock, to_backend)

        while True:
            gevent.sleep(1.)


class Blackout(BaseHandler):
    """Just closes the client socket on every call.
    """
    name = 'hang'
    options = {}

    def __call__(self, client_sock, backend_sock, to_backend):
        """Don't do anything -- the sockets get closed
        """
        client_sock.close()


handlers = {'dummy': Dummy(),
            'delay': Delay(),
            'error': Error(),
            'hang': Hang(),
            'blackout': Blackout()}
