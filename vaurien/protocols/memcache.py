import re

from vaurien.protocols.base import BaseProtocol
from vaurien.util import chunked


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)
RE_KEEPALIVE = re.compile('Connection: Keep-Alive')
RE_MEMCACHE_COMMAND = re.compile('(.*)\r\n')

EOH = '\r\n\r\n'
CRLF = '\r\n'


class Memcache(BaseProtocol):
    """Memcache protocol.
    """
    name = 'memcache'

    def _handle(self, source, dest, to_backend):
        # https://github.com/memcached/memcached/blob/master/doc/protocol.txt
        # Sending the query
        buffer = self._get_data(source)
        if not buffer:
            self._abort_handling(to_backend, dest)
            return

        # sending the first packet
        dest.sendall(buffer)

        # finding the command we sent.
        cmd = RE_MEMCACHE_COMMAND.search(buffer)

        if cmd is None:
            # wat ?
            self._abort_handling(to_backend, dest)
            return

        # looking at the command
        cmd = cmd.groups()[0]
        buffer_size = self.option('buffer')

        cmd_parts = cmd.split()
        mcmd = cmd_parts[0]

        if mcmd in ('set', 'add', 'replace', 'append'):
            cmd_size = len(cmd) + len(CRLF)
            data_size = int(cmd_parts[-1])
            total_size = cmd_size + data_size

            # grabbing more data if needed
            left_to_read = total_size - len(buffer) + len(CRLF)
            if left_to_read > 0:
                for chunk in chunked(left_to_read, buffer_size):
                    data = source.recv(chunk)
                    buffer += data
                    dest.sendall(data)

        # Receiving the response now
        buffer = self._get_data(dest, buffer_size)
        source.sendall(buffer)

        if buffer.startswith('VALUE'):
            # we're getting back a value.
            EOW = 'END' + CRLF
        else:
            EOW = CRLF

        while not buffer.endswith(EOW):
            data = self._get_data(dest, buffer_size)
            buffer += data
            source.sendall(data)

        # we're done
        return True    # keeping connected
