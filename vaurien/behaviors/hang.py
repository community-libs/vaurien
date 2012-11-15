import gevent

from vaurien.behaviors.dummy import Dummy
from vaurien.util import get_data


class Hang(Dummy):
    """Reads the packets that have been sent then hangs.

    Acts like a *pdb.set_trace()* you'd forgot in your code ;)
    """
    name = 'hang'
    options = {}

    def on_before_handle(self, protocol, source, dest, to_backend):
        # consume the socket and hang
        data = get_data(source)
        while data:
            data = get_data(source)

        while True:
            gevent.sleep(1.)
