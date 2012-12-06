import re

from vaurien.protocols.base import BaseProtocol
from vaurien.util import chunked


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)
RE_KEEPALIVE = re.compile('Connection: Keep-Alive')
RE_MEMCACHE_COMMAND = re.compile('(.*)\r\n')

EOH = '\r\n\r\n'
CRLF = '\r\n'


class Http(BaseProtocol):
    """HTTP protocol.
    """
    name = 'http'

    def _handle(self, source, dest, to_backend):
        buffer_size = self.option('buffer')

        # Getting the HTTP query
        data = self._get_data(source)

        if not data:
            self._abort_handling(to_backend, dest)
            return False

        # sending it to the backend
        dest.sendall(data)

        # Receiving the response
        buffer = self._get_data(dest, buffer_size)

        source.sendall(buffer)

        # Reading the HTTP Headers
        while EOH not in buffer:
            data = self._get_data(dest, buffer_size)
            buffer += data
            source.sendall(data)

        # keep alive header ?
        keep_alive = RE_KEEPALIVE.search(buffer) is not None

        # content-length header - to see if we need to suck more
        # data.
        match = RE_LEN.search(buffer)
        if match:
            resp_len = int(match.group(1))
            left_to_read = resp_len - len(buffer)
            if left_to_read > 0:
                for chunk in chunked(left_to_read, buffer_size):
                    data = self._get_data(dest, chunk)
                    buffer += data
                    source.sendall(data)
        else:
            # embarrassing...
            # just sucking until recv() returns ''
            while True:
                data = self._get_data(dest, buffer_size)
                if data == '':
                    break
                source.sendall(data)

        # do we close the client ?
        if not keep_alive and not self.option('keep_alive'):
            source.close()
            source._closed = True

        if not self.option('reuse_socket') and not self.option('keep_alive'):
            dest.close()
            dest._closed = True

        # we're done
        return keep_alive or self.option('keep_alive')
