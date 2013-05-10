from vaurien.behaviors.dummy import Dummy


class Blackout(Dummy):
    """Immediately closes client socket, no other actions taken.

    """
    name = 'blackout'
    options = {}

    def on_before_handle(self, protocol, source, dest, to_backend):
        # close source socket
        source.close()
        source._closed = True
        return False
