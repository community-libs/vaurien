import re

from vaurien.protocols.base import BaseProtocol


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)
RE_KEEPALIVE = re.compile('Connection: Keep-Alive')
RE_MEMCACHE_COMMAND = re.compile('(.*)\r\n')

EOH = '\r\n\r\n'
CRLF = '\r\n'


class TCP(BaseProtocol):
    """TCP handler.
    """
    name = 'tcp'

    def _handle(self, source, dest, to_backend):
        # default TCP behavior
        data = self._get_data(source)
        if data:
            dest.sendall(data)

            # If we are not keeping the connection alive
            # we can suck the answer back and close the socket
            if not self.option('keep_alive'):
                # just suck it until it's empty
                data = ''
                while True:
                    data = self._get_data(dest)
                    if data == '':
                        break
                    source.sendall(data)

                if not self.option('reuse_socket'):
                    dest.close()
                    dest._closed = True

                # we're done - False means we'll disconnect the client
                return False

        return data != ''
