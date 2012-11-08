import gevent
from vaurien.handlers.dummy import Dummy


class Delay(Dummy):
    """Adds a delay before the backend is called.

    The delay can happen *after* or *before* the backend is called.
    """
    name = 'delay'
    options = {'sleep': ("Delay in seconds", int, 1),
               'before':
               ("If True adds before the backend is called. Otherwise"
                " after", bool, True),
               'keep_alive': ("Keep-alive protocol",
                              bool, False),
               'reuse_socket': ("If True, the socket is reused.",
                                bool, False)}

    def __call__(self, client_sock, backend_sock, to_backend):
        before = to_backend and self.option('before')
        after = not to_backend and not self.option('before')

        if before:
            gevent.sleep(self.option('sleep'))

        res = super(Delay, self).__call__(client_sock, backend_sock,
                                          to_backend)

        if after:
            gevent.sleep(self.option('sleep'))

        return res
