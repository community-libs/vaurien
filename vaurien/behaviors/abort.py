import socket
import re

from vaurien.behaviors.dummy import Dummy
from vaurien.util import get_data
from vaurien.protocols.http import Http

class Abort(Dummy):
    """Simulate an aborted connection by a client before receiving a response.
    """
    name = 'abort'

    def on_between_handle(self, protocol, source, dest, to_backend):
        dest.shutdown(socket.SHUT_RDWR)
        dest.close()

        return False
