from vaurien.handlers.base import BaseHandler


class Blackout(BaseHandler):
    """Just closes the client socket on every call.
    """
    name = 'blackout'
    options = {}

    def __call__(self, source, dest, to_backend):
        """Don't do anything -- the sockets get closed
        """
        source.close()
        source._closed = True
        return False
