import re

from vaurien.protocols.base import BaseProtocol
from vaurien.util import chunked


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)
RE_KEEPALIVE = re.compile('Connection: Keep-Alive')
RE_MEMCACHE_COMMAND = re.compile('(.*)\r\n')

EOH = '\r\n\r\n'
CRLF = '\r\n'


class Redis(BaseProtocol):
    """HTTP handler.
    """
    name = 'redis'

    def _handle(self, source, dest, to_backend):
        """ see http://redis.io/topics/protocol
        """
        # Getting the request.
        buffer = self._get_data(source)
        if not buffer:
            self._abandon(to_backend, dest)
            return

        # Sending the request to the backend.
        self.on_before_send_data(source, dest)
        dest.sendall(buffer)

        # Getting the answer back and sending it over.
        buffer_size = self.option('buffer')
        buffer = dest.recv(buffer_size)
        source.sendall(buffer)
        already_read = len(buffer)

        if buffer[0] in ('+', '-', ':'):
            # simple reply, we're good
            return False    # disconnect mode ?

        if buffer[0] == '$':
            # bulk reply
            size = int(buffer[1:buffer.find(CRLF)])
            left_to_read = size - already_read

            if left_to_read > 0:
                for chunk in chunked(left_to_read, buffer_size):
                    data = source.recv(chunk)
                    buffer += data
                    dest.sendall(data)

            return False  # disconnect mode ?

        if buffer[0] == '*':
            # multi-bulk reply
            raise NotImplementedError()

        raise NotImplementedError()
