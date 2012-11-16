from vaurien.behaviors.dummy import Dummy


class Blackout(Dummy):
    """Reads the packets that have been sent then hangs.

    Acts like a *pdb.set_trace()* you'd forgot in your code ;)
    """
    name = 'blackout'
    options = {}

    def on_before_handle(self, protocol, source, dest, to_backend):
        # consume the socket and hang
        source.close()
        source._closed = True
        return False
