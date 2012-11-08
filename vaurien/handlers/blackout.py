from vaurien.handlers.base import BaseHandler


class Blackout(BaseHandler):
    """Just closes the client socket on every call.
    """
    name = 'blackout'
    options = {}

    def __call__(self, client_sock, backend_sock, to_backend):
        """Don't do anything -- the sockets get closed
        """
        client_sock.close()
        return False
