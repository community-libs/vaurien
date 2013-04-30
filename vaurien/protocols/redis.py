import re

from vaurien.protocols.base import BaseProtocol
from vaurien.util import chunked


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)
RE_KEEPALIVE = re.compile('Connection: Keep-Alive')
RE_MEMCACHE_COMMAND = re.compile('(.*)\r\n')

EOH = '\r\n\r\n'
CRLF = '\r\n'


class Redis(BaseProtocol):
    """Redis protocol.
    """
    name = 'redis'

    def _find(self, source, buffer, char, dest):
        pos = buffer.find(char)
        while pos == -1:
            data = self._get_data(source)
            if data == '':
                return -1, buffer
            dest.sendall(data)
            buffer += data
            pos = buffer.find(char)
        return pos, buffer

    def _handle(self, source, dest, to_backend):
        """ see http://redis.io/topics/protocol
        """
        # grabbing data
        bytepos, buffer = self._find(source, '', CRLF, dest)
        if bytepos == -1:
            return False

        num_args = int(buffer[1:bytepos])

        for arg in range(num_args):
            # next CRLF
            buffer = buffer[bytepos + len(CRLF):]
            bytepos, buffer = self._find(source, buffer, CRLF, dest)

            # reading the number of bytes
            num_bytes = int(buffer[1:bytepos])
            data_start = bytepos + len(CRLF)

            # reading the data (next CRLF)
            buffer = buffer[data_start:]
            __, buffer = self._find(source, buffer, CRLF, dest)
            data = buffer[:num_bytes]
            bytepos = num_bytes

        # Getting the answer back and sending it over.
        buffer = self._get_data(dest)
        source.sendall(buffer)

        if buffer[0] in ('+', '-', ':'):
            # simple reply, we're good
            return False    # disconnect mode ?

        buffer_size = self.option('buffer')
        bytepos, buffer = self._find(dest, buffer, CRLF, source)

        if buffer[0] == '$':
            # bulk reply
            size = int(buffer[1:bytepos])
            left_to_read = (size - len(buffer) + len(buffer[:bytepos]) +
                            len(CRLF) * 2)

            if left_to_read > 0:
                for chunk in chunked(left_to_read, buffer_size):
                    data = self._get_data(dest, chunk)
                    buffer += data
                    source.sendall(data)

            return False  # disconnect mode ?

        if buffer[0] == '*':
            # multi-bulk reply
            raise NotImplementedError()

        raise NotImplementedError()
