import re

try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

from vaurien.protocols.base import BaseProtocol
from vaurien.util import chunked


HOST_REPLACE = re.compile(r'\r\nHost: .+\r\n')
CRLF = '\r\n'


class Http(BaseProtocol):
    """HTTP protocol.
    """
    name = 'http'

    def _handle(self, source, dest, to_backend):
        buffer_size = self.option('buffer')

        # Getting the HTTP query
        data = self._get_data(source)
        data = HOST_REPLACE.sub('\r\nHost: %s\r\n' % self.proxy.backend, data)

        if not data:
            self._abort_handling(to_backend, dest)
            return False

        # sending it to the backend
        dest.sendall(data)

        parser = HttpParser()
        while not parser.is_message_complete():
          data = self._get_data(dest, buffer_size)
          parser.execute(data, len(data))
          source.sendall(data)

        keep_alive = parser.should_keep_alive()

        # do we close the client ?
        if not keep_alive and not self.option('keep_alive'):
            source.close()
            source._closed = True

        if not self.option('reuse_socket') and not self.option('keep_alive'):
            dest.close()
            dest._closed = True

        # we're done
        return keep_alive or self.option('keep_alive')
