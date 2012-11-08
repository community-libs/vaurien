import os
from vaurien.handlers.dummy import Dummy


class Error(Dummy):
    """Reads the packets that have been sent then send random data in
    the socket.

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
            return super(Error, self).__call__(client_sock, backend_sock,
                                               to_backend)

        data = self._get_data(client_sock, backend_sock, to_backend)
        if not data:
            return False

        dest = to_backend and backend_sock or client_sock

        if self.option('inject'):
            if not to_backend:      # back to the client
                middle = len(data) / 2
                dest.sendall(data[:middle] + os.urandom(100) + data[middle:])
            else:                   # sending the data tp the backend
                dest.sendall(data)

        else:
            if not to_backend:
                # XXX find how to handle errors (which errors should we send)
                # depends on the protocol
                dest.sendall(os.urandom(1000))

            else:          # sending the data tp the backend
                dest.sendall(data)

        return True
